"""Simulate a day of BODE shading at a location.

    python -m bode_shade --lat 33.45 --lon -112.07 --date 2026-07-15 --tz -7
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from .power import Airframe, SolarCanopy, clear_sky_irradiance_w_m2, flight_time_min, hover_power_w, solar_power_w
from .shade import User, solve_shade
from .solar import sun_position


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lat", type=float, default=33.45, help="latitude (default: Phoenix)")
    p.add_argument("--lon", type=float, default=-112.07, help="longitude, east positive")
    p.add_argument("--date", default="2026-07-15", help="YYYY-MM-DD local date")
    p.add_argument("--tz", type=float, default=-7, help="UTC offset in hours")
    args = p.parse_args()

    tz = timezone(timedelta(hours=args.tz))
    day = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=tz)
    frame, canopy = Airframe(), SolarCanopy()
    user = User(position=(0.0, 0.0, 0.0))

    print(f"BODE shade plan  lat={args.lat} lon={args.lon}  {args.date} (UTC{args.tz:+g})")
    print(f"hover draw {hover_power_w(frame):.0f} W | battery-only flight {flight_time_min(frame):.0f} min\n")
    print(f"{'time':>5} {'sun el':>7} {'sun az':>7} {'mode':>8} {'E':>6} {'N':>6} {'up':>5} {'tilt':>5} {'solar W':>8} {'flight':>7}")
    for hour in range(6, 21):
        when = day + timedelta(hours=hour)
        sun = sun_position(when, args.lat, args.lon)
        sol = solve_shade(sun, user)
        solar = solar_power_w(canopy, clear_sky_irradiance_w_m2(sun.elevation_deg)) if sun.is_up and sol.mode != "perch" else 0.0
        if sol.target is None:
            pos = f"{'-':>6} {'-':>6} {'-':>5}"
            flight = "-"
        else:
            e, n, u = sol.target
            pos = f"{e:6.2f} {n:6.2f} {u:5.2f}"
            ft = flight_time_min(frame, solar)
            flight = "inf" if ft == float("inf") else f"{ft:.0f}m"
        print(
            f"{when:%H:%M} {sun.elevation_deg:7.1f} {sun.azimuth_deg:7.1f} {sol.mode:>8} {pos} "
            f"{sol.canopy_tilt_deg:5.1f} {solar:8.0f} {flight:>7}"
        )


if __name__ == "__main__":
    main()
