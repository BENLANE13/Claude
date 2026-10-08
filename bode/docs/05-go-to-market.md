# Go-to-Market: Campus Wars

## Launch sequence
1. **Waitlist race (now).** The website ranks campuses by signups. The top 3 hot-climate campuses get the pilots. Students recruit each other to win a pilot slot for their school.
2. **Pilot (fall semester).** 60 drones and 3 Roosts on one campus. Free first ride for everyone and 50% off Campus Pass for the first 1,000 signups.
3. **Campus Wars Season 1 (spring).** 3 campuses compete. Shade-minutes, distance, and per-capita leaderboards (all live in the app). The winning school gets the Golden Canopy trophy and $10,000 to its student fund.
4. **Expand.** 15 campuses, BODE for Teams at commencement and tailgates.

## Campus Wars mechanics
- Every ride's GPS path is drawn on the map and scored: **10 points per shade-minute**, doubled for Campus Pass riders.
- Anti-cheat: segments faster than 6 m/s (vehicles, GPS jumps) don't count, and shade only counts when the sun is above 8°. Both are implemented in `bode_link.fleet`.
- Leaderboards: total shade-minutes, total km, and shade-minutes per 100 students (so small schools can win).
- Individual badges: "Solstice" (longest walk on the hottest day), "Eclipse" (100 rides).

## Channels
| Channel | Tactic |
|---|---|
| Campus ambassadors | 10 paid students per campus; referral codes count toward Campus Wars |
| Social | Drone-follow videos are inherently shareable; a weekly leaderboard drop on TikTok and Instagram |
| University | Pitch to sustainability, student affairs, and heat-safety offices; co-branded canopies |
| Partners | Scooter apps list BODE through GBFS and hand off riders via BODE Link (see `06-partner-integration.md`) |
| Press | "Drone umbrellas arrive on campus" stories; first-day launch event |

## Brand voice
Cool, plain, a little playful. "Shade that follows you." No jargon in rider copy. Riders don't need to hear about GBFS or azimuths.
