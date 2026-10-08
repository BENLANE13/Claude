import math
import unittest
from datetime import datetime, timezone

from bode_shade import (
    Airframe,
    ShadeConfig,
    SolarCanopy,
    SunPosition,
    clear_sky_irradiance_w_m2,
    User,
    flight_time_min,
    hover_power_w,
    shadow_center_on_head_plane,
    solar_power_w,
    solve_shade,
    sun_position,
)


class SolarTests(unittest.TestCase):
    def test_summer_solstice_noon_at_40n(self):
        # Solar noon at lon 0 is ~12:02 UTC on 2024-06-20; elevation = 90 - 40 + 23.44.
        sun = sun_position(datetime(2024, 6, 20, 12, 2, tzinfo=timezone.utc), 40.0, 0.0)
        self.assertAlmostEqual(sun.elevation_deg, 73.44, delta=0.3)
        self.assertAlmostEqual(sun.azimuth_deg, 180.0, delta=3.0)

    def test_morning_sun_is_east_and_afternoon_west(self):
        morning = sun_position(datetime(2024, 9, 22, 8, 0, tzinfo=timezone.utc), 51.5, 0.0)
        evening = sun_position(datetime(2024, 9, 22, 16, 0, tzinfo=timezone.utc), 51.5, 0.0)
        self.assertTrue(60 < morning.azimuth_deg < 150)
        self.assertTrue(210 < evening.azimuth_deg < 300)

    def test_night(self):
        sun = sun_position(datetime(2024, 6, 20, 0, 0, tzinfo=timezone.utc), 40.0, 0.0)
        self.assertFalse(sun.is_up)

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            sun_position(datetime(2024, 1, 1), 0, 0)


class ShadeTests(unittest.TestCase):
    def assert_shadow_hits_head(self, sun, user, cfg=ShadeConfig()):
        sol = solve_shade(sun, user, cfg)
        head = user.head(cfg.lead_time_s)
        sx, sy = shadow_center_on_head_plane(sol.target, sun, head[2])
        self.assertAlmostEqual(sx, head[0], places=6)
        self.assertAlmostEqual(sy, head[1], places=6)
        return sol

    def test_overhead_sun_hovers_directly_above(self):
        sol = self.assert_shadow_hits_head(SunPosition(89.99, 0.0), User((3.0, 4.0, 0.0)))
        self.assertAlmostEqual(sol.target[0], 3.0, places=2)
        self.assertAlmostEqual(sol.target[1], 4.0, places=2)
        self.assertEqual(sol.mode, "shade")

    def test_drone_sits_on_the_sun_side(self):
        # Sun due east at 45 deg: drone must be east of the user by exactly its clearance.
        sol = self.assert_shadow_hits_head(SunPosition(45.0, 90.0), User((0.0, 0.0, 0.0)))
        self.assertGreater(sol.target[0], 0)
        self.assertAlmostEqual(sol.target[1], 0.0, places=6)
        self.assertAlmostEqual(sol.standoff_m, sol.clearance_m, places=6)

    def test_canopy_faces_the_sun(self):
        sol = solve_shade(SunPosition(30.0, 200.0), User((0, 0, 0)))
        self.assertAlmostEqual(sol.canopy_tilt_deg, 60.0)
        self.assertAlmostEqual(sol.canopy_facing_deg, 200.0)

    def test_low_sun_reduces_clearance_to_respect_standoff(self):
        cfg = ShadeConfig()
        sol = self.assert_shadow_hits_head(SunPosition(15.0, 270.0), User((0, 0, 0)), cfg)
        self.assertLessEqual(sol.standoff_m, cfg.max_standoff_m + 1e-9)
        self.assertGreaterEqual(sol.clearance_m, cfg.min_clearance_m)

    def test_tight_standoff_gives_partial_shade(self):
        cfg = ShadeConfig(max_standoff_m=2.5)
        sol = solve_shade(SunPosition(15.0, 270.0), User((0, 0, 0)), cfg)
        self.assertEqual(sol.mode, "partial")
        self.assertTrue(0.0 < sol.shade_coverage < 1.0)
        self.assertAlmostEqual(sol.clearance_m, cfg.min_clearance_m)

    def test_shade_cylinder_still_covers_head_when_slightly_short(self):
        # At 9 deg the canopy can't reach the ideal spot, but the head is still inside the shadow tube.
        sol = solve_shade(SunPosition(9.0, 270.0), User((0, 0, 0)))
        self.assertEqual(sol.mode, "shade")
        self.assertEqual(sol.shade_coverage, 1.0)

    def test_sun_below_threshold_perches(self):
        sol = solve_shade(SunPosition(3.0, 270.0), User((0, 0, 0)))
        self.assertEqual(sol.mode, "perch")
        self.assertIsNone(sol.target)

    def test_leads_a_walking_user(self):
        cfg = ShadeConfig(lead_time_s=1.0)
        still = solve_shade(SunPosition(60, 180), User((0, 0, 0)), cfg)
        walking = solve_shade(SunPosition(60, 180), User((0, 0, 0), velocity=(1.4, 0, 0)), cfg)
        self.assertAlmostEqual(walking.target[0] - still.target[0], 1.4, places=6)


class PowerTests(unittest.TestCase):
    def test_hover_power_plausible_for_1_6kg_quad(self):
        self.assertTrue(120 < hover_power_w(Airframe()) < 260)

    def test_solar_extends_flight(self):
        frame, canopy = Airframe(), SolarCanopy()
        self.assertGreater(flight_time_min(frame, solar_power_w(canopy)), 2 * flight_time_min(frame))

    def test_off_angle_canopy_makes_less_power(self):
        canopy = SolarCanopy()
        self.assertAlmostEqual(solar_power_w(canopy, incidence_deg=60), solar_power_w(canopy) / 2, places=6)

    def test_clear_sky_irradiance(self):
        self.assertTrue(900 < clear_sky_irradiance_w_m2(90) < 1100)
        self.assertLess(clear_sky_irradiance_w_m2(10), clear_sky_irradiance_w_m2(60))
        self.assertEqual(clear_sky_irradiance_w_m2(-5), 0.0)

    def test_flight_time_infinite_when_solar_covers_hover(self):
        self.assertEqual(flight_time_min(Airframe(), solar_w=10_000), math.inf)


if __name__ == "__main__":
    unittest.main()
