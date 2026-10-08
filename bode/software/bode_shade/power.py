"""Energy budget: how much of the hover power can the solar canopy supply?

Hover power uses momentum theory: P_ideal = T^1.5 / sqrt(2 * rho * A).
Real rotors reach a figure of merit around 0.6-0.7, and the motor/ESC chain
loses another ~15-20%.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.81
AIR_DENSITY = 1.225  # kg/m^3, sea level


@dataclass(frozen=True)
class Airframe:
    mass_kg: float = 1.65
    rotor_count: int = 4
    rotor_diameter_m: float = 0.254  # 10 inch props
    figure_of_merit: float = 0.65
    drivetrain_efficiency: float = 0.82
    avionics_w: float = 8.0  # flight controller, cameras, compute, radios
    battery_wh: float = 74.0  # 4S 5000 mAh
    usable_battery_fraction: float = 0.8


@dataclass(frozen=True)
class SolarCanopy:
    diameter_m: float = 1.0
    cell_efficiency: float = 0.23  # flexible monocrystalline / back-contact
    fill_factor: float = 0.85  # fraction of the disc covered by active cells
    mppt_efficiency: float = 0.95


def hover_power_w(frame: Airframe, air_density: float = AIR_DENSITY) -> float:
    thrust = frame.mass_kg * G
    disc_area = frame.rotor_count * math.pi * (frame.rotor_diameter_m / 2) ** 2
    ideal = thrust**1.5 / math.sqrt(2 * air_density * disc_area)
    return ideal / (frame.figure_of_merit * frame.drivetrain_efficiency) + frame.avionics_w


def solar_power_w(canopy: SolarCanopy, irradiance_w_m2: float = 1000.0, incidence_deg: float = 0.0) -> float:
    """Electrical power from the canopy. incidence 0 = canopy facing the sun squarely."""
    area = math.pi * (canopy.diameter_m / 2) ** 2
    cos_i = max(0.0, math.cos(math.radians(incidence_deg)))
    return area * canopy.fill_factor * canopy.cell_efficiency * canopy.mppt_efficiency * irradiance_w_m2 * cos_i


def flight_time_min(frame: Airframe, solar_w: float = 0.0) -> float:
    """Minutes of hover on one battery, with solar offsetting the draw."""
    net = hover_power_w(frame) - solar_w
    if net <= 0:
        return math.inf
    return frame.battery_wh * frame.usable_battery_fraction / net * 60.0


def clear_sky_irradiance_w_m2(sun_elevation_deg: float) -> float:
    """Direct-beam irradiance on a sun-facing surface (Meinel model, Kasten-Young air mass)."""
    if sun_elevation_deg <= 0:
        return 0.0
    zenith = 90.0 - sun_elevation_deg
    air_mass = 1.0 / (math.cos(math.radians(zenith)) + 0.50572 * (96.07995 - zenith) ** -1.6364)
    return 1353.0 * 0.7 ** (air_mass**0.678)
