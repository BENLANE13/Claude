"""Sun position from time and location.

Implements the NOAA solar position algorithm (Meeus-based). Accuracy is
roughly 0.01 deg for elevation and azimuth between 1800 and 2100, which is far
tighter than the canopy needs to place a shadow on a person.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SunPosition:
    elevation_deg: float  # angle above the horizon (negative = below)
    azimuth_deg: float  # clockwise from true north, 0..360

    @property
    def is_up(self) -> bool:
        return self.elevation_deg > 0.0

    def unit_vector(self) -> tuple[float, float, float]:
        """Unit vector pointing *toward* the sun in local East-North-Up axes."""
        el = math.radians(self.elevation_deg)
        az = math.radians(self.azimuth_deg)
        return (math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))


def _julian_day(when: datetime) -> float:
    when = when.astimezone(timezone.utc)
    return when.timestamp() / 86400.0 + 2440587.5


def sun_position(when: datetime, lat_deg: float, lon_deg: float) -> SunPosition:
    """Sun elevation/azimuth for a timezone-aware datetime at lat/lon (east positive)."""
    if when.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")

    jc = (_julian_day(when) - 2451545.0) / 36525.0

    mean_long = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0
    mean_anom = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    ecc = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)

    m = math.radians(mean_anom)
    eq_center = (
        math.sin(m) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + math.sin(2 * m) * (0.019993 - 0.000101 * jc)
        + math.sin(3 * m) * 0.000289
    )
    true_long = mean_long + eq_center
    omega = math.radians(125.04 - 1934.136 * jc)
    app_long = true_long - 0.00569 - 0.00478 * math.sin(omega)

    mean_obliq = 23.0 + (26.0 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60.0) / 60.0
    obliq = math.radians(mean_obliq + 0.00256 * math.cos(omega))

    decl = math.asin(math.sin(obliq) * math.sin(math.radians(app_long)))

    y = math.tan(obliq / 2.0) ** 2
    l0 = math.radians(mean_long)
    eq_time_min = 4.0 * math.degrees(
        y * math.sin(2 * l0)
        - 2 * ecc * math.sin(m)
        + 4 * ecc * y * math.sin(m) * math.cos(2 * l0)
        - 0.5 * y * y * math.sin(4 * l0)
        - 1.25 * ecc * ecc * math.sin(2 * m)
    )

    utc = when.astimezone(timezone.utc)
    minutes = utc.hour * 60 + utc.minute + utc.second / 60.0 + utc.microsecond / 6e7
    true_solar_min = (minutes + eq_time_min + 4.0 * lon_deg) % 1440.0
    hour_angle = math.radians(true_solar_min / 4.0 - 180.0)

    lat = math.radians(lat_deg)
    cos_zen = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(hour_angle)
    zenith = math.acos(max(-1.0, min(1.0, cos_zen)))

    denom = math.cos(lat) * math.sin(zenith)
    if abs(denom) < 1e-12:
        azimuth = 180.0  # sun at zenith or observer at a pole; azimuth is undefined
    else:
        cos_az = (math.sin(lat) * math.cos(zenith) - math.sin(decl)) / denom
        az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
        azimuth = (az + 180.0) % 360.0 if hour_angle > 0 else (540.0 - az) % 360.0

    return SunPosition(elevation_deg=90.0 - math.degrees(zenith), azimuth_deg=azimuth)
