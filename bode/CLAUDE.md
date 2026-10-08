# BODE: notes for Claude

- Business: Lime-style shared solar shade drones on college campuses, with a Campus Wars competition and partner integrations (GBFS + BODE Link API).
- Brand: Eclipse Violet `#6B3BFF`, Unbounded / Instrument Sans / JetBrains Mono. See `brand/BRAND.md`. Copy is plain and rider-focused.
- Code is standard-library Python only (no pip installs). Run tests from `bode/software`: `python3 -m unittest discover -s tests`.
- `bode_shade` is pure math; `bode_link/fleet.py` is pure logic; `bode_link/server.py` is a thin HTTP layer. Keep that split.
- Keep claims honest: solar *extends* flight (~75% of hover power at noon), it does not sustain hover. Sample/leaderboard data on the website is labeled as sample.
- Numbers in docs come from `financials/model.py` and `bode_shade`; rerun them if assumptions change.
