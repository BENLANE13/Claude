# BODE: notes for Claude

- Business: Lime-style shared solar shade drones on college campuses, with GPS path tracking and partner integrations (GBFS + BODE Link API). Campus Wars (school-vs-school competition) was dropped; don't reintroduce it. Fun-feature proposals live in `docs/09-fun-features.md`.
- Brand: Eclipse Violet `#6B3BFF`, Unbounded / Instrument Sans / JetBrains Mono. See `brand/BRAND.md`. Copy is plain and rider-focused.
- Code is standard-library Python only (no pip installs). Run tests from `bode/software`: `python3 -m unittest discover -s tests`.
- `bode_shade` is pure math; `bode_link/fleet.py` is pure logic; `bode_link/server.py` is a thin HTTP layer. Keep that split.
- Keep claims honest: solar *extends* flight (~75% of hover power at noon), it does not sustain hover. Example data on the website (like the ride receipt) is labeled as an example.
- Numbers in docs come from `financials/model.py` and `bode_shade`; rerun them if assumptions change.
