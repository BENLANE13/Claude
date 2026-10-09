# Business Plan

## One line
BODE runs shared fleets of solar shade drones on hot college campuses. Riders unlock one in the app and it follows them, holding the angle that keeps them in shade. The model is Lime's, applied to shade.

## Lean canvas

| | |
|---|---|
| **Problem** | Long, unshaded walks in extreme heat; umbrellas are impractical; fixed shade doesn't move |
| **Customer** | Students at Sun Belt campuses (riders); universities (hosts and sponsors); event organizers |
| **Unique value** | Hands-free shade that follows you and aims at the sun. The solar canopy gives about 4× normal drone flight time |
| **Solution** | AI drone + solar canopy + Roost charging stations + rider app with walk maps |
| **Channels** | Campus ambassadors, social video, university partnerships, scooter-app integrations (BODE Link) |
| **Revenue** | $1 unlock + $0.25/min; $14.99/mo Campus Pass; campus sponsorships (~$25–35k/campus/yr); BODE for Teams |
| **Costs** | Drones (~$1,100 falling to $700), Roosts, field ops, insurance, remote pilots, software |
| **Key metrics** | Rides per drone per day, shade-minutes, drone payback days, incidents per 10k flight-hours |
| **Unfair advantage** | Solar-shade control loop (provisional patent planned), FAA operational approvals, campus exclusivity |

## Business model (Lime-style)
- Drones live on **Roosts**: solar perches with chargers, placed near libraries, unions, and rec centers.
- Riders unlock in the app. The nearest drone launches, finds them, and shades them. When the ride ends it flies back to the nearest Roost.
- Campus Pass riders get unlimited 20-minute rides and priority unlocks during heat advisories.
- Partners (scooter apps) book escorts through the BODE Link API and earn 15% of those rides.

## Unit economics (from `financials/model.py`)

| | 2027 | 2028 | 2029 |
|---|---|---|---|
| Campuses | 3 | 15 | 45 |
| Fleet | 180 | 900 | 2,700 |
| Rides | 108k | 979k | 3.7M |
| Revenue | $0.35M | $2.9M | $10.9M |
| Contribution margin | 57% | 62% | 64% |
| EBITDA | –$2.5M | –$4.7M | –$6.0M |
| Drone payback | 115 days | 65 days | 47 days |

Cumulative cash needed before profitability is about **$16M** (EBITDA plus fleet capex), so the plan is a seed round followed by a Series A. Fleet capex can be partly debt-financed because drones are financeable assets.

## Funding plan
| Round | Amount | Use | Milestone |
|---|---|---|---|
| Pre-seed / Shark | $500k | 60-drone pilot fleet, FAA approvals, app | 1 campus live, 10k rides |
| Seed | $3M | 3 campuses | 100k rides, measured payback |
| Series A | $15M | 15 campuses, BODE for Teams | Contribution-positive campuses |

## Biggest risks and mitigations
| Risk | Mitigation |
|---|---|
| FAA approval for flights over people | Design to Part 107 Category 3; start on private campus property; remote-pilot oversight; engage the FAA early |
| Safety incident | Ducted rotors, parachute, geofences, conservative wind limits, insurance |
| Weather seasonality | Launch in the Sun Belt; redeploy fleets to events off-season |
| Vandalism and theft | Drones live on elevated Roosts, never on the ground; GPS tracking |
| Noise complaints | Quiet hours, large slow props, campus-controlled no-fly zones |
| Unit cost | Contract manufacturing quotes before the seed round; design for a $700 BOM |
