"""Fleet, trips with path tracking, and partner escorts. Pure logic, no I/O.

The HTTP layer in server.py is a thin wrapper around FleetService so the
same rules can later move behind a real database without changing tests.
"""

from __future__ import annotations

import math
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone

from bode_shade import sun_position

EARTH_RADIUS_M = 6_371_000.0
UNLOCK_FEE = 1.00
PER_MINUTE = 0.25
MIN_SHADE_ELEVATION_DEG = 8.0
MAX_WALKING_SPEED_MPS = 6.0  # faster than this between points = GPS jump or vehicle; not counted
PARTNER_REV_SHARE = 0.15


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


@dataclass
class Campus:
    id: str
    name: str
    lat: float
    lon: float


@dataclass
class Roost:
    id: str
    campus_id: str
    name: str
    lat: float
    lon: float
    capacity: int = 6


@dataclass
class Drone:
    id: str
    campus_id: str
    lat: float
    lon: float
    battery_pct: float = 100.0
    status: str = "available"  # available | reserved | in_use | returning | maintenance
    roost_id: str | None = None


@dataclass
class TrackPoint:
    lat: float
    lon: float
    t: datetime


@dataclass
class Trip:
    id: str
    rider_id: str
    campus_id: str
    drone_id: str
    started_at: datetime
    has_pass: bool = False
    partner_id: str | None = None
    path: list[TrackPoint] = field(default_factory=list)
    distance_m: float = 0.0
    shade_minutes: float = 0.0
    ended_at: datetime | None = None
    price_usd: float | None = None

    def summary(self) -> dict:
        return {
            "trip_id": self.id,
            "rider_id": self.rider_id,
            "campus_id": self.campus_id,
            "drone_id": self.drone_id,
            "partner_id": self.partner_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "distance_m": round(self.distance_m, 1),
            "shade_minutes": round(self.shade_minutes, 2),
            "price_usd": self.price_usd,
            "path": [[p.lat, p.lon] for p in self.path],
        }


@dataclass
class Escort:
    id: str
    partner_id: str
    rider_ref: str
    trip_id: str
    drone_id: str
    status: str
    eta_seconds: int
    price_estimate_usd: float


class FleetError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class FleetService:
    def __init__(self) -> None:
        self.campuses: dict[str, Campus] = {}
        self.roosts: dict[str, Roost] = {}
        self.drones: dict[str, Drone] = {}
        self.trips: dict[str, Trip] = {}
        self.escorts: dict[str, Escort] = {}
        self.partners: dict[str, str] = {}  # api key -> partner id
        self.webhooks: dict[str, list[str]] = {}  # partner id -> urls
        self.events: list[tuple[str, dict]] = []  # (partner_id, payload) outbox for webhook delivery

    # --- setup ---------------------------------------------------------------

    def add_campus(self, campus: Campus) -> None:
        self.campuses[campus.id] = campus

    def add_roost(self, roost: Roost, drones: int) -> None:
        self.roosts[roost.id] = roost
        for i in range(drones):
            d = Drone(id=f"BODE-{roost.id.upper()}-{i + 1:02d}", campus_id=roost.campus_id, lat=roost.lat, lon=roost.lon, roost_id=roost.id)
            self.drones[d.id] = d

    def register_partner(self, partner_id: str) -> str:
        key = f"pk_{secrets.token_hex(12)}"
        self.partners[key] = partner_id
        return key

    def partner_for_key(self, key: str | None) -> str:
        if not key or key not in self.partners:
            raise FleetError(401, "missing or unknown X-Partner-Key")
        return self.partners[key]

    # --- trips -----------------------------------------------------------------

    def nearest_available(self, campus_id: str, lat: float, lon: float) -> Drone:
        candidates = [d for d in self.drones.values() if d.campus_id == campus_id and d.status == "available" and d.battery_pct >= 30]
        if not candidates:
            raise FleetError(409, "no BODE available on this campus right now")
        return min(candidates, key=lambda d: haversine_m(lat, lon, d.lat, d.lon))

    def start_trip(self, rider_id: str, campus_id: str, lat: float, lon: float, *, has_pass: bool = False,
                   partner_id: str | None = None, at: datetime | None = None) -> Trip:
        if campus_id not in self.campuses:
            raise FleetError(404, f"unknown campus {campus_id}")
        drone = self.nearest_available(campus_id, lat, lon)
        drone.status = "in_use"
        drone.roost_id = None
        trip = Trip(id=_id("trip"), rider_id=rider_id, campus_id=campus_id, drone_id=drone.id,
                    started_at=at or _now(), has_pass=has_pass, partner_id=partner_id)
        self.trips[trip.id] = trip
        return trip

    def _trip(self, trip_id: str) -> Trip:
        trip = self.trips.get(trip_id)
        if trip is None:
            raise FleetError(404, f"unknown trip {trip_id}")
        return trip

    def add_points(self, trip_id: str, points: list[TrackPoint]) -> Trip:
        """Append GPS points to a trip's path, adding up distance and shade-minutes."""
        trip = self._trip(trip_id)
        if trip.ended_at:
            raise FleetError(409, "trip already ended")
        for p in sorted(points, key=lambda p: p.t):
            if trip.path:
                prev = trip.path[-1]
                dt = (p.t - prev.t).total_seconds()
                if dt <= 0:
                    continue
                d = haversine_m(prev.lat, prev.lon, p.lat, p.lon)
                if d / dt <= MAX_WALKING_SPEED_MPS:
                    trip.distance_m += d
                    sun = sun_position(p.t, p.lat, p.lon)
                    if sun.elevation_deg >= MIN_SHADE_ELEVATION_DEG:
                        trip.shade_minutes += dt / 60.0
            trip.path.append(p)
            drone = self.drones[trip.drone_id]
            drone.lat, drone.lon = p.lat, p.lon
        return trip

    def end_trip(self, trip_id: str, at: datetime | None = None) -> Trip:
        trip = self._trip(trip_id)
        if trip.ended_at:
            return trip
        trip.ended_at = at or _now()
        minutes = max(1, math.ceil((trip.ended_at - trip.started_at).total_seconds() / 60))
        trip.price_usd = 0.0 if trip.has_pass and minutes <= 20 else round(UNLOCK_FEE + PER_MINUTE * minutes, 2)

        drone = self.drones[trip.drone_id]
        drone.status = "returning"
        roost = min((r for r in self.roosts.values() if r.campus_id == trip.campus_id),
                    key=lambda r: haversine_m(drone.lat, drone.lon, r.lat, r.lon))
        drone.lat, drone.lon, drone.roost_id, drone.status = roost.lat, roost.lon, roost.id, "available"

        for escort in self.escorts.values():
            if escort.trip_id == trip.id:
                escort.status = "returned"
                self._emit(escort, extra={"trip": trip.summary(), "partner_share_usd": round((trip.price_usd or 0) * PARTNER_REV_SHARE, 2)})
        return trip

    # --- Partner escorts (BODE Link) ----------------------------------------------

    def request_escort(self, partner_id: str, rider_ref: str, campus_id: str, lat: float, lon: float,
                       max_minutes: int = 15) -> Escort:
        trip = self.start_trip(rider_id=f"{partner_id}:{rider_ref}", campus_id=campus_id, lat=lat, lon=lon, partner_id=partner_id)
        drone = self.drones[trip.drone_id]
        dist = haversine_m(lat, lon, drone.lat, drone.lon)
        escort = Escort(id=_id("esc"), partner_id=partner_id, rider_ref=rider_ref, trip_id=trip.id, drone_id=drone.id,
                        status="dispatched", eta_seconds=int(15 + dist / 8.0),  # 8 m/s cruise plus launch
                        price_estimate_usd=round(UNLOCK_FEE + PER_MINUTE * max_minutes, 2))
        self.escorts[escort.id] = escort
        self._emit(escort)
        return escort

    def escort(self, escort_id: str, partner_id: str) -> Escort:
        e = self.escorts.get(escort_id)
        if e is None or e.partner_id != partner_id:
            raise FleetError(404, f"unknown escort {escort_id}")
        return e

    def set_escort_status(self, escort_id: str, partner_id: str, status: str) -> Escort:
        if status not in ("arrived", "shading", "cancelled"):
            raise FleetError(400, "status must be arrived, shading, or cancelled")
        e = self.escort(escort_id, partner_id)
        e.status = status
        if status == "cancelled":
            self.end_trip(e.trip_id)
            e.status = "cancelled"
        else:
            self._emit(e)
        return e

    def _emit(self, escort: Escort, extra: dict | None = None) -> None:
        payload = {"event": f"escort.{escort.status}", "escort": escort_json(escort), "at": _now().isoformat()}
        if extra:
            payload.update(extra)
        self.events.append((escort.partner_id, payload))

    # --- GBFS feeds -----------------------------------------------------------------

    def gbfs(self, base_url: str) -> dict:
        feeds = ["system_information", "station_information", "station_status", "vehicle_status", "vehicle_types"]
        return {
            "last_updated": _now().isoformat(timespec="seconds"),
            "ttl": 30,
            "version": "3.0",
            "data": {"feeds": [{"name": f, "url": f"{base_url}/gbfs/{f}.json"} for f in feeds]},
        }

    def gbfs_feed(self, name: str) -> dict:
        now = _now().isoformat(timespec="seconds")
        if name == "system_information":
            data = {"system_id": "bode", "languages": ["en"], "name": [{"text": "BODE", "language": "en"}],
                    "opening_hours": "Mo-Su 07:00-19:00", "feed_contact_email": "partners@bode.example",
                    "timezone": "America/Phoenix"}
        elif name == "vehicle_types":
            data = {"vehicle_types": [{"vehicle_type_id": "bode-one", "form_factor": "other",
                                       "propulsion_type": "electric", "name": [{"text": "BODE One shade drone", "language": "en"}],
                                       "max_range_meters": 6000}]}
        elif name == "station_information":
            data = {"stations": [{"station_id": r.id, "name": [{"text": r.name, "language": "en"}],
                                  "lat": r.lat, "lon": r.lon, "capacity": r.capacity} for r in self.roosts.values()]}
        elif name == "station_status":
            data = {"stations": [{"station_id": r.id, "is_installed": True, "is_renting": True, "is_returning": True,
                                  "last_reported": now,
                                  "num_vehicles_available": sum(1 for d in self.drones.values() if d.roost_id == r.id and d.status == "available"),
                                  "num_docks_available": r.capacity - sum(1 for d in self.drones.values() if d.roost_id == r.id)}
                                 for r in self.roosts.values()]}
        elif name == "vehicle_status":
            data = {"vehicles": [{"vehicle_id": d.id, "lat": d.lat, "lon": d.lon, "is_reserved": d.status != "available",
                                  "is_disabled": d.status == "maintenance", "vehicle_type_id": "bode-one",
                                  "current_fuel_percent": round(d.battery_pct / 100, 2), "station_id": d.roost_id,
                                  "rental_uris": {"web": f"https://bode.example/unlock/{d.id}"}}
                                 for d in self.drones.values()]}
        else:
            raise FleetError(404, f"unknown GBFS feed {name}")
        return {"last_updated": now, "ttl": 30, "version": "3.0", "data": data}


def escort_json(e: Escort) -> dict:
    return {"escort_id": e.id, "partner_id": e.partner_id, "rider_ref": e.rider_ref, "trip_id": e.trip_id,
            "drone_id": e.drone_id, "status": e.status, "eta_seconds": e.eta_seconds,
            "price_estimate_usd": e.price_estimate_usd}


def demo_fleet() -> FleetService:
    """Three pilot campuses with Roosts, for local development and the rider app demo."""
    svc = FleetService()
    campuses = [
        Campus("tempe", "Tempe pilot campus", 33.4242, -111.9281),
        Campus("austin", "Austin pilot campus", 30.2849, -97.7341),
        Campus("gainesville", "Gainesville pilot campus", 29.6436, -82.3549),
    ]
    offsets = [(0.0015, -0.002, "Library Roost"), (-0.002, 0.0012, "Union Roost"), (0.0005, 0.003, "Rec Center Roost")]
    for c in campuses:
        svc.add_campus(c)
        for i, (dlat, dlon, name) in enumerate(offsets):
            svc.add_roost(Roost(f"{c.id}-r{i + 1}", c.id, name, c.lat + dlat, c.lon + dlon), drones=4)
    return svc
