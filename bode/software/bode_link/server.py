"""BODE Link HTTP server (standard library only).

    cd bode/software && python3 -m bode_link.server --port 8080
    open http://localhost:8080/app/

Rider endpoints:   POST /v1/trips, POST /v1/trips/{id}/points, POST /v1/trips/{id}/end, GET /v1/trips/{id}
Campuses:          GET  /v1/campuses
Partner endpoints: POST /v1/escorts, GET /v1/escorts/{id}, POST /v1/escorts/{id}/status, POST /v1/webhooks
                   (all need the X-Partner-Key header)
Open data:         GET  /gbfs/gbfs.json and the feeds it lists
Rider web app:     GET  /app/
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .fleet import FleetError, FleetService, TrackPoint, demo_fleet, escort_json

APP_DIR = Path(__file__).resolve().parents[2] / "app"


def _parse_time(value) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000 if value > 1e11 else value, tz=timezone.utc)
    t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _require(body: dict, *keys: str) -> None:
    missing = [k for k in keys if k not in body]
    if missing:
        raise FleetError(400, f"missing field(s): {', '.join(missing)}")


def deliver_webhooks(svc: FleetService) -> None:
    """Best-effort delivery of queued partner events. Production uses a durable queue with retries and signing."""
    while svc.events:
        partner_id, payload = svc.events.pop(0)
        for url in svc.webhooks.get(partner_id, []):
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            threading.Thread(target=lambda r=req: _post_quietly(r), daemon=True).start()


def _post_quietly(req: urllib.request.Request) -> None:
    try:
        urllib.request.urlopen(req, timeout=5).close()
    except Exception:
        pass


def make_handler(svc: FleetService):
    class Handler(BaseHTTPRequestHandler):
        server_version = "BODELink/0.1"

        def log_message(self, fmt, *args):  # quieter console
            pass

        # --- helpers -------------------------------------------------------------
        def _send(self, status: int, payload) -> None:
            body = json.dumps(payload, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if not n:
                return {}
            try:
                data = json.loads(self.rfile.read(n))
            except json.JSONDecodeError:
                raise FleetError(400, "body must be JSON")
            if not isinstance(data, dict):
                raise FleetError(400, "body must be a JSON object")
            return data

        def _base_url(self) -> str:
            return f"http://{self.headers.get('Host', 'localhost')}"

        def _static(self, rel: str) -> None:
            path = (APP_DIR / (rel or "index.html")).resolve()
            if APP_DIR not in path.parents and path != APP_DIR or not path.is_file():
                raise FleetError(404, "not found")
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Partner-Key")
            self.end_headers()

        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        # --- routing ---------------------------------------------------------------
        def _dispatch(self, method: str) -> None:
            url = urlparse(self.path)
            parts = [p for p in url.path.split("/") if p]
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                status, payload = self._route(method, parts, query)
                if status == 0:
                    return  # static file already written
                self._send(status, payload)
                deliver_webhooks(svc)
            except FleetError as e:
                self._send(e.status, {"error": e.message})

        def _route(self, method: str, parts: list[str], query: dict):
            if method == "GET" and (not parts or parts == ["app"]) and not self.path.startswith("/app/"):
                self.send_response(302)
                self.send_header("Location", "/app/")
                self.end_headers()
                return 0, None
            if method == "GET" and parts[:1] == ["app"]:
                self._static("/".join(parts[1:]))
                return 0, None

            if parts[:1] == ["gbfs"] and method == "GET":
                if parts[1:] == ["gbfs.json"]:
                    return 200, svc.gbfs(self._base_url())
                if len(parts) == 2 and parts[1].endswith(".json"):
                    return 200, svc.gbfs_feed(parts[1][:-5])

            if parts[:1] != ["v1"]:
                raise FleetError(404, "not found")
            r = parts[1:]

            # Campuses
            if method == "GET" and r == ["campuses"]:
                return 200, {"campuses": [{"campus_id": c.id, "name": c.name, "lat": c.lat, "lon": c.lon} for c in svc.campuses.values()]}

            # Rider trips
            if method == "POST" and r == ["trips"]:
                b = self._body()
                _require(b, "rider_id", "campus_id", "lat", "lon")
                trip = svc.start_trip(b["rider_id"], b["campus_id"], float(b["lat"]), float(b["lon"]), has_pass=bool(b.get("has_pass")))
                return 201, trip.summary()
            if len(r) >= 2 and r[0] == "trips":
                if method == "GET" and len(r) == 2:
                    return 200, svc._trip(r[1]).summary()
                if method == "POST" and r[2:] == ["points"]:
                    b = self._body()
                    _require(b, "points")
                    pts = [TrackPoint(float(p["lat"]), float(p["lon"]), _parse_time(p.get("t"))) for p in b["points"]]
                    return 200, svc.add_points(r[1], pts).summary()
                if method == "POST" and r[2:] == ["end"]:
                    return 200, svc.end_trip(r[1]).summary()

            # Partners (BODE Link)
            if r[:1] in (["escorts"], ["webhooks"]):
                partner = svc.partner_for_key(self.headers.get("X-Partner-Key"))
                if method == "POST" and r == ["webhooks"]:
                    b = self._body()
                    _require(b, "url")
                    svc.webhooks.setdefault(partner, []).append(str(b["url"]))
                    return 201, {"partner_id": partner, "webhooks": svc.webhooks[partner]}
                if method == "POST" and r == ["escorts"]:
                    b = self._body()
                    _require(b, "rider_ref", "campus_id", "pickup")
                    e = svc.request_escort(partner, str(b["rider_ref"]), b["campus_id"], float(b["pickup"]["lat"]),
                                           float(b["pickup"]["lon"]), int(b.get("max_minutes", 15)))
                    return 201, escort_json(e)
                if method == "GET" and len(r) == 2:
                    return 200, escort_json(svc.escort(r[1], partner))
                if method == "POST" and len(r) == 3 and r[2] == "status":
                    b = self._body()
                    _require(b, "status")
                    return 200, escort_json(svc.set_escort_status(r[1], partner, b["status"]))

            raise FleetError(404, "not found")

    return Handler


def main() -> None:
    p = argparse.ArgumentParser(description="Run the BODE Link API and rider app locally.")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()
    svc = demo_fleet()
    key = svc.register_partner("demo-scooter-app")
    print(f"BODE Link on http://localhost:{args.port}  (rider app at /app/, GBFS at /gbfs/gbfs.json)")
    print(f"Demo partner key: {key}")
    ThreadingHTTPServer(("", args.port), make_handler(svc)).serve_forever()


if __name__ == "__main__":
    main()
