"""Where to fly so the canopy's shadow lands on the user.

Frame: local East-North-Up metres, origin anywhere on flat ground.

The shadow of a point P falls along the ray from P away from the sun. To put
the canopy's shadow on the user's head, the canopy centre must sit on the
ray from the head *toward* the sun, at some clearance above the head:

    canopy = head + sun_dir * (clearance / sin(elevation))

Low sun pushes the drone far out sideways (horizontal standoff grows as
clearance / tan(elevation)). We cap standoff for safety and line-of-sight,
lowering clearance first, then reporting partial shade if even the minimum
clearance cannot be reached.

The canopy is tilted to face the sun. That single choice both maximises the
shadow cast and maximises solar power into the panel, which is the core of
BODE's design: the angle that shades you is the angle that charges it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .solar import SunPosition

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class ShadeConfig:
    canopy_radius_m: float = 0.5
    min_clearance_m: float = 1.2  # never closer than this above the head
    preferred_clearance_m: float = 2.0
    max_standoff_m: float = 6.0  # max horizontal distance from the user
    max_altitude_m: float = 8.0
    min_sun_elevation_deg: float = 8.0  # below this, shade is impractical: perch instead
    lead_time_s: float = 0.6  # predict the user ahead by control-loop latency


@dataclass(frozen=True)
class User:
    position: Vec3  # feet on the ground (z = 0 for flat terrain)
    height_m: float = 1.75
    velocity: Vec3 = (0.0, 0.0, 0.0)

    def head(self, lead_time_s: float = 0.0) -> Vec3:
        x, y, z = self.position
        vx, vy, vz = self.velocity
        t = lead_time_s
        return (x + vx * t, y + vy * t, z + vz * t + self.height_m)


@dataclass(frozen=True)
class ShadeSolution:
    mode: str  # "shade", "partial", or "perch"
    target: Vec3 | None  # canopy centre position
    canopy_tilt_deg: float  # tilt from horizontal
    canopy_facing_deg: float  # azimuth the canopy normal points to
    clearance_m: float  # distance above the head along the vertical
    standoff_m: float  # horizontal distance from the head
    shade_coverage: float  # fraction of a head-sized disc that is shaded (0..1)
    notes: list[str] = field(default_factory=list)


def _head_coverage(miss_m: float, canopy_radius_m: float, head_radius_m: float = 0.12) -> float:
    """Rough fraction of the head inside the shadow, given shadow-centre miss distance."""
    if miss_m <= canopy_radius_m - head_radius_m:
        return 1.0
    if miss_m >= canopy_radius_m + head_radius_m:
        return 0.0
    return (canopy_radius_m + head_radius_m - miss_m) / (2 * head_radius_m)


def solve_shade(sun: SunPosition, user: User, cfg: ShadeConfig = ShadeConfig()) -> ShadeSolution:
    """Compute the canopy pose that shades the user's head."""
    if sun.elevation_deg < cfg.min_sun_elevation_deg:
        return ShadeSolution(
            mode="perch",
            target=None,
            canopy_tilt_deg=0.0,
            canopy_facing_deg=sun.azimuth_deg,
            clearance_m=0.0,
            standoff_m=0.0,
            shade_coverage=0.0,
            notes=[f"sun elevation {sun.elevation_deg:.1f} deg below {cfg.min_sun_elevation_deg} deg; perch and charge"],
        )

    el = math.radians(sun.elevation_deg)
    tan_el = math.tan(el)
    head = user.head(cfg.lead_time_s)
    notes: list[str] = []

    clearance = cfg.preferred_clearance_m
    clearance = min(clearance, cfg.max_altitude_m - head[2])
    standoff = clearance / tan_el
    if standoff > cfg.max_standoff_m:
        clearance = cfg.max_standoff_m * tan_el
        standoff = cfg.max_standoff_m
        notes.append("low sun: clearance reduced to respect max standoff")

    mode = "shade"
    coverage = 1.0
    if clearance < cfg.min_clearance_m:
        # Hold minimum clearance at max standoff; the shadow lands short of the head.
        clearance = cfg.min_clearance_m
        standoff = cfg.max_standoff_m
        ideal_standoff = clearance / tan_el
        miss = ideal_standoff - standoff
        # Projected onto the ground plane the shadow is stretched by 1/sin(el); compare on the head plane.
        coverage = _head_coverage(miss * math.sin(el), cfg.canopy_radius_m)
        mode = "shade" if coverage >= 1.0 else "partial" if coverage > 0 else "perch"
        notes.append(f"held at minimum clearance; shadow axis is {miss * math.sin(el):.2f} m from the head")

    sx, sy, _ = sun.unit_vector()
    horiz = math.hypot(sx, sy) or 1.0
    target = (
        head[0] + sx / horiz * standoff,
        head[1] + sy / horiz * standoff,
        head[2] + clearance,
    )

    return ShadeSolution(
        mode=mode,
        target=target,
        canopy_tilt_deg=90.0 - sun.elevation_deg,
        canopy_facing_deg=sun.azimuth_deg,
        clearance_m=clearance,
        standoff_m=standoff,
        shade_coverage=coverage,
        notes=notes,
    )


def shadow_center_on_head_plane(canopy: Vec3, sun: SunPosition, head_z: float) -> tuple[float, float]:
    """Project the canopy centre along the sun ray down to the plane z = head_z."""
    sx, sy, sz = sun.unit_vector()
    t = (canopy[2] - head_z) / sz
    return (canopy[0] - sx * t, canopy[1] - sy * t)
