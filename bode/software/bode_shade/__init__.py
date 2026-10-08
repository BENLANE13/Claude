"""BODE shade engine: sun position, shade positioning, and energy budget."""

from .power import Airframe, SolarCanopy, clear_sky_irradiance_w_m2, flight_time_min, hover_power_w, solar_power_w
from .shade import ShadeConfig, ShadeSolution, User, shadow_center_on_head_plane, solve_shade
from .solar import SunPosition, sun_position

__all__ = [
    "Airframe",
    "ShadeConfig",
    "ShadeSolution",
    "SolarCanopy",
    "SunPosition",
    "User",
    "clear_sky_irradiance_w_m2",
    "flight_time_min",
    "hover_power_w",
    "shadow_center_on_head_plane",
    "solar_power_w",
    "solve_shade",
    "sun_position",
]
