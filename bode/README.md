# BODE: Shade That Follows You

BODE runs Lime-style shared fleets of solar-powered AI drones on hot college campuses. Unlock one in the app and it flies to you, then holds the exact angle between you and the sun so you walk in shade. Its canopy is a solar panel: **the angle that shades you is the angle that charges it**, which gives about 80-minute flights instead of 20.

## What's here
| Path | What |
|---|---|
| `docs/` | Market research, business plan, product spec, regulatory, go-to-market, partner integration, **pitches**, launch checklist |
| `brand/` | Logo (SVG), color, type, voice |
| `website/` | Marketing site ([live preview](https://claude.ai/artifact/8rcrd6uA536sNF8PFQaQFU)) |
| `app/` | Rider web app: live map, unlock, GPS path tracking, Campus Wars leaderboard |
| `software/bode_shade/` | Sun position, shade positioning solver, solar/flight energy model |
| `software/bode_link/` | Fleet + trips + Campus Wars + partner escort API + GBFS feeds + HTTP server |
| `financials/` | 3-year fleet financial model (`model.py` → `pnl.csv`) |

## Run it
```bash
cd bode/software
python3 -m unittest discover -s tests          # 33 tests
python3 -m bode_shade                           # hour-by-hour shade plan for a Phoenix July day
python3 -m bode_link.server --port 8080         # then open http://localhost:8080/app/
cd ../financials && python3 model.py            # P&L
```
Python 3.10+ and no third-party packages. The rider app loads Leaflet and OpenStreetMap tiles from the internet.
