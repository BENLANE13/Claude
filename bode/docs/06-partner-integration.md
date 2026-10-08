# Working With Lime and Other Micromobility Apps

BODE is built to complement scooter and bike apps, not compete with them. A scooter gets you most of the way, and BODE shades the walk from the drop zone to the door.

## What exists today (open standards we use)
- **GBFS** (General Bikeshare Feed Specification) is the open format scooter and bike fleets, Lime included, publish so trip planners can show vehicles. BODE publishes a **GBFS v3 feed** of its Roosts (`station_information`, `station_status`) and drones (`vehicle_status`). Any app that reads GBFS can show BODEs on its map without a custom deal.
- **MDS** (Mobility Data Specification) is what cities use to regulate fleets. BODE can report to it if a city requires it.

## BODE Link API (built in `software/bode_link`)
| Endpoint | Purpose |
|---|---|
| `GET /gbfs/gbfs.json` | Feed index (public) |
| `POST /v1/escorts` | Partner books a BODE for its rider at a pickup point → escort id, drone, ETA, price estimate |
| `GET /v1/escorts/{id}` | Escort status |
| `POST /v1/escorts/{id}/status` | Partner marks `arrived`, `shading`, or `cancelled` |
| `POST /v1/webhooks` | Partner registers a URL for `escort.dispatched / shading / returned` events. The `returned` event includes the trip summary and the partner's 15% revenue share |
| `GET /v1/campuses/leaderboard` | Partner apps can show Campus Wars standings |

Partner calls need an `X-Partner-Key` header. Partners can only see their own escorts (tested).

### Example: ride handoff
```
1. Rider ends a scooter ride near the library.
2. Scooter app: POST /v1/escorts { rider_ref, campus_id, pickup:{lat,lon}, max_minutes }
3. BODE dispatches the nearest drone → webhook escort.dispatched (ETA 48 s)
4. Drone arrives, shading starts → webhook escort.shading
5. Rider reaches the building, ride ends → webhook escort.returned with fare and partner share
```

## What an actual Lime partnership requires (business steps)
Lime doesn't offer a public API for third parties to book rides, so integration beyond GBFS needs a business-development deal:
1. Build traction first: BODE live on at least one campus where Lime also operates.
2. Approach Lime's partnerships team with the handoff proposal: more Lime rides end near buildings (riders don't need to park at the door), plus revenue share on BODE rides.
3. Start with a deep-link pilot: a "Get shade for the rest of your walk" button in the Lime ride-end screen opens `bode://escort?...`. This needs no API changes on their side.
4. Graduate to server-to-server escorts using BODE Link.

The same playbook applies to Veo, Bird, Spin, and university bikeshare programs, many of which already publish GBFS.
