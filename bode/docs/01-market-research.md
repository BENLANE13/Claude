# Market Research

## The problem
Sun Belt campuses (Arizona, Texas, Florida, Southern California, Georgia, Nevada) regularly exceed 100°F during the fall and late-spring semesters. Students walk 2–5 km a day between buildings with little continuous shade. Heat illness, sunburn, and plain discomfort are common. Umbrellas need a free hand and aren't carried on sunny days, and fixed shade structures cover only small areas.

## Market size

| Layer | Estimate | Basis |
|---|---|---|
| Global consumer drone market (2025) | ~$6–13B | Published estimates vary by firm and definition: Fortune Business Insights $5.9B, Mordor $6.2B, Grand View $12.8B |
| Growth | ~9–13% CAGR | Mordor: $7.1B (2026) to $13.1B (2031); Grand View: 8.8% CAGR to 2033 |
| **TAM** (shared shade on US campuses + events) | ~$1.2B/yr | ~4M students at hot-climate 4-year campuses × ~$300/yr potential spend |
| **SAM** (Sun Belt campuses >20k students) | ~$400M/yr | ~120 campuses |
| **SOM** (year 3, 45 campuses) | ~$11M/yr | from `financials/model.py` |

The TAM/SAM figures are top-down assumptions to be validated with waitlist and pilot data.

## Competition and prior art

| Who | What | Status | BODE's difference |
|---|---|---|---|
| **Free Parasol** (Asahi Power Service, Japan) | DJI Mavic plus an umbrella that follows by GPS, ~$275 | Concept shown 2018; ~5-minute flight; aimed at private venues like golf courses; no confirmed shipping | Solar canopy gives ~80-minute flights; sun-angle positioning instead of fixed overhead; a fleet model |
| **John Tse's autonomous umbrella** (DIY, Canada) | Depth-camera head tracking, Raspberry Pi | Maker project, not commercial | A commercial fleet with ops, safety, and insurance |
| Lime / Bird / Veo | Shared scooters and bikes | Large fleets, open GBFS data | Potential partner, not competitor: BODE covers the walk after the ride |
| Umbrellas, hats, campus shade structures | Passive shade | Ubiquitous | Hands-free, moves with you, aims at the sun |

**Takeaway:** the idea has been prototyped, but nobody has solved flight time or built a business model. BODE's two key differences are the solar canopy (flight time) and the shared fleet (price and ops).

## Customer segments (in launch order)
1. **Students on hot campuses.** The core rider: price-sensitive, social, and competitive (Campus Wars).
2. **Universities.** Sponsors and hosts. They want heat-safety measures, sustainability stories, and recruiting buzz.
3. **Events.** Graduations, tailgates, festivals, golf tournaments (BODE for Teams).
4. **Outdoor workers.** Grounds crews, construction, and agriculture, driven by heat-safety rules. A later B2B line.

## Validation plan (before building 180 drones)
- [ ] 30 student interviews on two hot campuses: would they pay $4 for a shaded 12-minute walk?
- [ ] Waitlist goal: 2,000 signups per pilot campus.
- [ ] Letters of intent from 3 universities (sustainability office or student affairs).
- [ ] Fake-door test: a "Reserve a BODE" button in campus Instagram ads, measuring click-through.

## Sources
- [Fortune Business Insights: consumer drone market](https://www.fortunebusinessinsights.com/consumer-drone-market-115477)
- [Technavio: consumer drones market](https://technavio.com/report/consumer-drones-market-industry-analysis)
- [The Drive: Free Parasol drone](https://www.thedrive.com/tech/21277/free-parasol-drone-keeps-you-shaded-and-hands-free)
- [Yanko Design: autonomous flying umbrella](https://www.yankodesign.com/?p=602903)
- [Electronics For You: drone umbrella tracks users](https://www.electronicsforu.com/news/drone-umbrella-tracks-users-autonomously)
