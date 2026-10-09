import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer

from bode_link import FleetError, TrackPoint, demo_fleet, haversine_m
from bode_link.server import make_handler

# 10:00 local in Tempe in July: sun well up.
MORNING = datetime(2026, 7, 15, 17, 0, tzinfo=timezone.utc)
NIGHT = datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc)


def walk(lat, lon, start, steps=10, step_s=10, dlat=0.0001):
    """A straight walk north at ~1.1 m/s."""
    return [TrackPoint(lat + i * dlat, lon, start + timedelta(seconds=i * step_s)) for i in range(steps + 1)]


class FleetTests(unittest.TestCase):
    def setUp(self):
        self.svc = demo_fleet()

    def test_haversine(self):
        self.assertAlmostEqual(haversine_m(0, 0, 0.001, 0), 111.2, delta=0.5)

    def test_trip_scores_distance_and_shade(self):
        trip = self.svc.start_trip("r1", "tempe", 33.4242, -111.9281, at=MORNING)
        self.svc.add_points(trip.id, walk(33.4242, -111.9281, MORNING))
        self.assertAlmostEqual(trip.distance_m, 111.2, delta=1.0)
        self.assertAlmostEqual(trip.shade_minutes, 100 / 60, places=3)

    def test_no_shade_credit_at_night(self):
        trip = self.svc.start_trip("r1", "tempe", 33.4242, -111.9281, at=NIGHT)
        self.svc.add_points(trip.id, walk(33.4242, -111.9281, NIGHT))
        self.assertGreater(trip.distance_m, 100)
        self.assertEqual(trip.shade_minutes, 0)

    def test_gps_jumps_and_vehicle_speed_are_not_scored(self):
        trip = self.svc.start_trip("r1", "tempe", 33.4242, -111.9281, at=MORNING)
        pts = [TrackPoint(33.4242, -111.9281, MORNING), TrackPoint(33.4342, -111.9281, MORNING + timedelta(seconds=10))]
        self.svc.add_points(trip.id, pts)
        self.assertEqual(trip.distance_m, 0)
        self.assertEqual(len(trip.path), 2)

    def test_end_trip_prices_and_returns_drone(self):
        trip = self.svc.start_trip("r1", "tempe", 33.4242, -111.9281, at=MORNING)
        self.svc.add_points(trip.id, walk(33.4242, -111.9281, MORNING, steps=60))
        self.svc.end_trip(trip.id, at=MORNING + timedelta(minutes=10))
        self.assertEqual(trip.price_usd, 3.50)  # $1 + 10 x $0.25
        self.assertEqual(self.svc.drones[trip.drone_id].status, "available")

    def test_campus_pass_rides_under_20_min_are_free(self):
        trip = self.svc.start_trip("r1", "tempe", 33.4242, -111.9281, has_pass=True, at=MORNING)
        self.svc.add_points(trip.id, walk(33.4242, -111.9281, MORNING, steps=30))
        self.svc.end_trip(trip.id, at=MORNING + timedelta(minutes=5))
        self.assertEqual(trip.price_usd, 0.0)

    def test_fleet_runs_out(self):
        for i in range(12):
            self.svc.start_trip(f"r{i}", "austin", 30.2849, -97.7341)
        with self.assertRaises(FleetError) as cm:
            self.svc.start_trip("late", "austin", 30.2849, -97.7341)
        self.assertEqual(cm.exception.status, 409)

    def test_escort_lifecycle_emits_events_with_partner_share(self):
        e = self.svc.request_escort("scooter-co", "r_1", "tempe", 33.4242, -111.9281)
        self.assertEqual(e.status, "dispatched")
        self.svc.set_escort_status(e.id, "scooter-co", "shading")
        self.svc.end_trip(e.trip_id)
        events = [p["event"] for _, p in self.svc.events]
        self.assertEqual(events, ["escort.dispatched", "escort.shading", "escort.returned"])
        self.assertIn("partner_share_usd", self.svc.events[-1][1])

    def test_partner_cannot_read_other_partners_escort(self):
        e = self.svc.request_escort("scooter-co", "r_1", "tempe", 33.4242, -111.9281)
        with self.assertRaises(FleetError):
            self.svc.escort(e.id, "someone-else")

    def test_gbfs_feeds(self):
        index = self.svc.gbfs("http://x")
        names = [f["name"] for f in index["data"]["feeds"]]
        for n in names:
            self.assertIn("data", self.svc.gbfs_feed(n))
        status = self.svc.gbfs_feed("station_status")["data"]["stations"]
        self.assertEqual(sum(s["num_vehicles_available"] for s in status), 36)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc = demo_fleet()
        cls.key = cls.svc.register_partner("scooter-co")
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.svc))
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def call(self, method, path, body=None, key=None):
        req = urllib.request.Request(self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **({"X-Partner-Key": key} if key else {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_rider_trip_over_http(self):
        s, trip = self.call("POST", "/v1/trips", {"rider_id": "u1", "campus_id": "gainesville", "lat": 29.6436, "lon": -82.3549})
        self.assertEqual(s, 201)
        pts = [{"lat": 29.6436 + i * 0.0001, "lon": -82.3549, "t": f"2026-07-15T15:00:{i * 10:02d}Z"} for i in range(6)]
        s, trip = self.call("POST", f"/v1/trips/{trip['trip_id']}/points", {"points": pts})
        self.assertEqual(s, 200)
        self.assertGreater(trip["distance_m"], 50)
        self.assertEqual(len(trip["path"]), 6)
        s, ended = self.call("POST", f"/v1/trips/{trip['trip_id']}/end")
        self.assertEqual(s, 200)
        self.assertGreater(ended["price_usd"], 0)
        self.assertEqual(len(ended["path"]), 6)

    def test_escort_needs_partner_key(self):
        s, err = self.call("POST", "/v1/escorts", {"rider_ref": "r", "campus_id": "tempe", "pickup": {"lat": 33.42, "lon": -111.93}})
        self.assertEqual(s, 401)

    def test_escort_over_http(self):
        s, e = self.call("POST", "/v1/escorts", {"rider_ref": "r9", "campus_id": "tempe", "pickup": {"lat": 33.4242, "lon": -111.9281}}, key=self.key)
        self.assertEqual(s, 201)
        self.assertEqual(e["status"], "dispatched")
        s, got = self.call("GET", f"/v1/escorts/{e['escort_id']}", key=self.key)
        self.assertEqual(got["drone_id"], e["drone_id"])

    def test_gbfs_over_http(self):
        s, idx = self.call("GET", "/gbfs/gbfs.json")
        self.assertEqual(s, 200)
        self.assertEqual(idx["version"], "3.0")
        s, v = self.call("GET", "/gbfs/vehicle_status.json")
        self.assertTrue(v["data"]["vehicles"])

    def test_bad_input_is_400_not_crash(self):
        s, err = self.call("POST", "/v1/trips", {"rider_id": "u1"})
        self.assertEqual(s, 400)
        self.assertIn("missing", err["error"])

    def test_rider_app_is_served(self):
        with urllib.request.urlopen(self.base + "/app/") as r:
            self.assertIn(b"BODE", r.read())


if __name__ == "__main__":
    unittest.main()
