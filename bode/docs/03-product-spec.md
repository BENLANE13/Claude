# Product Spec: BODE One

## Hardware (target)
| Part | Spec |
|---|---|
| Airframe | Quad, 1.65 kg all-up, 10" props in ducts mounted *outside* the canopy rim |
| Canopy | 1.0 m disc, flexible 23%-efficient cells, 85% fill; tilt gimbal 0–80° |
| Battery | 4S 5000 mAh (74 Wh), hot-swappable at Roosts |
| Sensors | GNSS + RTK (on campus), downward ToF/depth camera for person tracking, IMU, barometer, anemometer |
| Compute | On-device vision (no video leaves the drone) |
| Safety | Remote ID broadcast, parachute, foam rim, geofence, return-to-Roost on low battery or high wind |
| Roost | Elevated solar perch, 6 drones, charging plus a weather shelter |

## The physics (verified in `software/bode_shade`)
- **Placement:** to shade a head, the canopy sits on the ray from the head toward the sun. At 2 m clearance and sun elevation *e*, horizontal standoff is 2 / tan(*e*).
- **Tilt:** the canopy faces the sun (tilt = 90° − *e*). This maximizes both the shadow cast and the solar power collected.
- **Shadow tube:** the shadow is a cylinder along the sun ray. The head stays shaded as long as it's within ~0.38 m of the ray axis, which gives the controller margin.
- **Low sun:** horizontal standoff is capped at 6 m. Below 8° sun elevation BODE perches, because the needed geometry becomes impractical.
- **Energy:** hover draw is ~181 W. The canopy delivers ~137 W at midday (clear sky), so **flight time goes from ~20 min to ~80 min**. Solar cannot fully sustain hover; this is stated honestly in every pitch.

Run `python -m bode_shade --lat 33.45 --lon -112.07 --date 2026-07-15 --tz -7` for an hour-by-hour plan.

## Software architecture
```
Rider app (app/)  ──HTTP──▶  BODE Link API (software/bode_link)  ◀──  Partner apps (Lime-style)
   │ map + GPS path              │ trips, Campus Wars, escorts           GBFS feeds, webhooks
   ▼                             ▼
OpenStreetMap / Leaflet      Fleet service ──▶ Drone autopilot (future: PX4 + bode_shade on board)
```
- `bode_shade`: sun position (NOAA), shade solver, energy model. Pure Python, tested.
- `bode_link`: fleet, trips, path tracking and scoring, leaderboards, partner escorts, GBFS v3 feeds, HTTP server.
- `app/`: rider web app with a live map, unlock flow, GPS path, and leaderboard.

## Next engineering milestones
1. Port the shade solver to the flight controller (PX4 offboard mode, 20 Hz).
2. Person tracking on depth camera; fuse with the rider phone's GPS.
3. Wind-gust compensation: hold the shadow on the head in 15 mph gusts.
4. Drop-test and impact-energy testing toward the Category 3 means of compliance.
5. Native iOS/Android apps (the web app is the reference).
