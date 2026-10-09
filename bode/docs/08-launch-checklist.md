# Launch Checklist: What's Done and What You Need to Do

These are the steps founders usually take when starting a company with Claude Code. Items marked ✅ were done in this repo. Items marked 🔲 need a person: money, signatures, accounts, or real-world meetings.

## Idea and research
- ✅ Market research, competitors, sizing (`01-market-research.md`)
- ✅ Feasibility check of the core physics: solar covers ~75% of hover power at noon (`software/bode_shade`)
- 🔲 30 student interviews on two hot campuses
- 🔲 Letters of intent from universities

## Business
- ✅ Business plan, lean canvas, risks (`02-business-plan.md`)
- ✅ 3-year financial model, runnable (`financials/model.py` → `pnl.csv`)
- ✅ Elevator pitch and Shark Tank pitch (`07-pitches.md`)
- 🔲 Turn the pitch into a slide deck (ask Claude: "make the BODE pitch deck")

## Brand
- ✅ Name, color (Eclipse Violet #6B3BFF), logo (`brand/`)
- 🔲 USPTO trademark search for "BODE"
- 🔲 Buy a domain (e.g. bode.co, flybode.com, getbode.com — check availability)
- 🔲 Social handles

## Product
- ✅ Shade-positioning engine with tests
- ✅ Fleet/trip backend with path tracking + partner API + GBFS feeds, with tests
- ✅ Fun feature proposals (`09-fun-features.md`); pick which to build
- ✅ Rider web app with live map and GPS path tracking (`app/`)
- ✅ Marketing website (`website/`, published as a claude.ai artifact)
- 🔲 Hire a drone hardware engineer or contract design firm; build 3 prototypes
- 🔲 Connect the waitlist form to a real backend (Formspree, Airtable, or a `/v1/waitlist` endpoint)
- 🔲 Deploy the website (Netlify, Vercel, or GitHub Pages) and the API (Fly.io, Render)

## Legal (needs a person and usually a lawyer)
- 🔲 Incorporate a Delaware C-corp (Stripe Atlas, Clerky, or a lawyer)
- 🔲 EIN, business bank account
- 🔲 Founder agreements and IP assignment
- 🔲 Provisional patent filing
- 🔲 Part 107 remote pilot certificate (founder or first hire)
- 🔲 Aviation and product liability insurance quotes
- 🔲 Privacy policy and terms of service

## Money
- 🔲 Apply to accelerators (Y Combinator, Techstars, university venture funds)
- 🔲 Pre-seed raise of $500k (Shark Tank casting applications are open on ABC's site)
