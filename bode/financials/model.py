"""BODE 3-year financial model: shared shade-drone fleet (Lime-style) on campuses.

Riders unlock a BODE from the app, it follows and shades them on their walk,
then returns to a solar Roost. Every number is an assumption to replace with
real quotes and pilot-campus data. Run:  python3 model.py  (writes pnl.csv)
"""

from __future__ import annotations

import csv
from pathlib import Path

# --- Fleet & demand --------------------------------------------------------

YEARS = [2027, 2028, 2029]
CAMPUSES = [3, 15, 45]  # live campuses at year end
DRONES_PER_CAMPUS = 60
AVG_FLEET_FRACTION = [0.5, 0.6, 0.65]  # campuses launch through the year
SEASON_DAYS = 200  # sunny, in-session days with flyable weather
RIDES_PER_DRONE_DAY = [6, 8, 9]  # walks are short: ~12 min
AVG_RIDE_MIN = 12

# --- Pricing (Lime-style) ----------------------------------------------------

UNLOCK_FEE = 1.00
PER_MINUTE = 0.25
PASS_SHARE_OF_RIDES = 0.45  # rides covered by the Campus Pass
PASS_PRICE_MONTH = 14.99
PASS_RIDES_PER_SUB_MONTH = 22
PARTNER_REFERRAL_SHARE = 0.10  # rides booked through partner apps (Lime etc.)
PARTNER_REV_SHARE = 0.15  # paid to the partner on those rides
CAMPUS_SPONSORSHIP = [25_000, 30_000, 35_000]  # per campus/yr: canopy branding, heat-safety contracts

# --- Unit costs ------------------------------------------------------------

DRONE_COST = [1_100, 850, 700]  # landed cost per drone
ROOST_COST_PER_CAMPUS = 18_000  # solar perch/charging stations
DRONE_LIFE_YEARS = 2.0
OPS_COST_PER_RIDE = 0.55  # field techs, swaps, cleaning, remote pilot oversight
INSURANCE_PER_DRONE_YEAR = 240  # aviation + product liability
PAYMENT_FEES_PCT = 0.04
CLOUD_PER_RIDE = 0.03

# --- Corporate opex ----------------------------------------------------------

HEADCOUNT = [10, 28, 60]
LOADED_COST_PER_HEAD = 160_000
RND_NON_PAYROLL = [600_000, 900_000, 1_200_000]
MARKETING = [250_000, 900_000, 2_000_000]  # Campus Wars season prizes, ambassadors
GA_NON_PAYROLL = [250_000, 500_000, 900_000]

# ---------------------------------------------------------------------------


def build() -> list[dict[str, float]]:
    rows = []
    fleet_capex_total = 0.0
    prev_campuses = 0
    for i, year in enumerate(YEARS):
        fleet_end = CAMPUSES[i] * DRONES_PER_CAMPUS
        new_drones = fleet_end - prev_campuses * DRONES_PER_CAMPUS
        avg_fleet = prev_campuses * DRONES_PER_CAMPUS + new_drones * AVG_FLEET_FRACTION[i]
        rides = avg_fleet * SEASON_DAYS * RIDES_PER_DRONE_DAY[i]

        payg_rides = rides * (1 - PASS_SHARE_OF_RIDES)
        payg_rev = payg_rides * (UNLOCK_FEE + PER_MINUTE * AVG_RIDE_MIN)
        pass_rev = rides * PASS_SHARE_OF_RIDES / PASS_RIDES_PER_SUB_MONTH * PASS_PRICE_MONTH
        sponsor_rev = CAMPUSES[i] * CAMPUS_SPONSORSHIP[i]
        ride_rev = payg_rev + pass_rev
        partner_cost = ride_rev * PARTNER_REFERRAL_SHARE * PARTNER_REV_SHARE
        revenue = ride_rev + sponsor_rev

        capex = new_drones * DRONE_COST[i] + (CAMPUSES[i] - prev_campuses) * ROOST_COST_PER_CAMPUS
        fleet_capex_total += capex
        depreciation = avg_fleet * DRONE_COST[min(i, len(DRONE_COST) - 1)] / DRONE_LIFE_YEARS

        cost_of_rides = (
            rides * (OPS_COST_PER_RIDE + CLOUD_PER_RIDE)
            + avg_fleet * INSURANCE_PER_DRONE_YEAR
            + ride_rev * PAYMENT_FEES_PCT
            + partner_cost
            + depreciation
        )
        contribution = revenue - cost_of_rides
        opex = HEADCOUNT[i] * LOADED_COST_PER_HEAD + RND_NON_PAYROLL[i] + MARKETING[i] + GA_NON_PAYROLL[i]
        ebitda = contribution + depreciation - opex

        rows.append(
            {
                "year": year,
                "campuses": CAMPUSES[i],
                "fleet_end": fleet_end,
                "rides": rides,
                "revenue_per_ride": ride_rev / rides,
                "ride_revenue": ride_rev,
                "sponsorship_revenue": sponsor_rev,
                "revenue": revenue,
                "cost_of_rides_incl_depreciation": cost_of_rides,
                "contribution": contribution,
                "contribution_margin_pct": 100 * contribution / revenue,
                "opex": opex,
                "ebitda": ebitda,
                "fleet_capex": capex,
                "drone_payback_days": DRONE_COST[i] / (ride_rev / avg_fleet / SEASON_DAYS - (cost_of_rides - depreciation) / avg_fleet / SEASON_DAYS),
            }
        )
        prev_campuses = CAMPUSES[i]
    return rows


def main() -> None:
    rows = build()
    out = Path(__file__).with_name("pnl.csv")
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()})

    print(f"{'':>34}" + "".join(f"{r['year']:>14}" for r in rows))
    for key in rows[0]:
        if key == "year":
            continue
        fmt = "{:>14,.2f}" if key in ("revenue_per_ride",) else "{:>14,.0f}"
        print(f"{key:>34}" + "".join(fmt.format(r[key]) for r in rows))

    running = trough = 0.0
    for r in rows:
        running += r["ebitda"] - r["fleet_capex"]
        trough = min(trough, running)
    print(f"\nPeak cumulative cash need (EBITDA - fleet capex): ${-trough:,.0f}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
