"""Generate the RiderDrop mini-sprint dataset. Stdlib only. Deterministic.

    python make_data.py          # writes ./data/*.csv
    python make_data.py --check  # same, then asserts every planted issue is present
"""
import csv, random, sys
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent / "data"
ZONES = ["Clifton", "Gulshan", "Korangi", "North Nazimabad"]
RIDERS = [f"R{i:02d}" for i in range(1, 26)]
START = datetime(2026, 9, 1)


def messy_zone(z):
    return random.choice([z, z.upper(), z.lower(), f"  {z} ", f"{z}  "])


def messy_date(d):
    return random.choice([d.strftime("%Y-%m-%d"), d.strftime("%d/%m/%Y"), d.strftime("%-d-%b-%Y") if sys.platform != "win32" else d.strftime("%d-%b-%Y").lstrip("0")])


def messy_money(x):
    return random.choice([f"Rs {x:,.0f}", f"{x:.2f}", f" {x:.0f} ", f"{x:,.2f}"])


parcels, scans, remits = [], [], []
truth = {}  # parcel_id -> (final_status, cod_due, delivered_dt)
scan_id = 0

for i in range(1, 1201):
    pid = f"P{i:05d}"
    booked = START + timedelta(days=random.randint(0, 25))
    promised = booked + timedelta(days=random.randint(2, 4))
    cod = 0 if random.random() < 0.15 else round(random.uniform(500, 15000), -1)
    zone, rider = random.choice(ZONES), random.choice(RIDERS)
    parcels.append({
        "parcel_id": pid, "booked_date": messy_date(booked),
        "promised_date": messy_date(promised), "zone": messy_zone(zone),
        "rider_id": rider, "cod_amount": f"{cod:.2f}",
        "updated_at": (booked + timedelta(hours=1)).isoformat(sep=" "),
    })

    # scan chain
    r = random.random()
    final = "delivered" if r < 0.80 else ("returned" if r < 0.92 else "in_transit")
    events = [("picked_up", booked + timedelta(hours=9, minutes=random.randint(0, 120)))]
    events.append(("in_transit", booked + timedelta(days=1, hours=random.randint(8, 14))))
    delivered_dt = None
    if final != "in_transit":
        delivered_dt = booked + timedelta(days=random.randint(1, 6), hours=random.randint(10, 19))
        events.append((final, delivered_dt))
    for status, ts in events:
        scan_id += 1
        scans.append({"scan_id": f"S{scan_id:06d}", "parcel_id": pid, "status": status,
                      "scanned_at": ts.isoformat(sep=" "), "rider_id": rider})
        if random.random() < 0.10:  # duplicate scan seconds apart
            scan_id += 1
            dup = ts + timedelta(seconds=random.randint(20, 100))
            scans.append({"scan_id": f"S{scan_id:06d}", "parcel_id": pid, "status": status,
                          "scanned_at": dup.isoformat(sep=" "), "rider_id": rider})

    truth[pid] = (final, cod if final == "delivered" else 0, delivered_dt, rider)

# planted issue: 40 duplicate parcel rows, later updated_at carries the real cod
dupes = random.sample(list(truth), 40)
for pid in dupes:
    row = dict(next(p for p in parcels if p["parcel_id"] == pid))
    row["updated_at"] = (datetime.fromisoformat(row["updated_at"]) + timedelta(days=1)).isoformat(sep=" ")
    row["zone"] = messy_zone(random.choice(ZONES))
    parcels.append(row)

# planted issue: 30 scans for parcels that do not exist
for _ in range(30):
    scan_id += 1
    scans.append({"scan_id": f"S{scan_id:06d}", "parcel_id": f"P9{random.randint(1000, 9999)}",
                  "status": "delivered", "scanned_at": (START + timedelta(days=random.randint(0, 25))).isoformat(sep=" "),
                  "rider_id": random.choice(RIDERS)})

# remittances
rid = 0
skimmers = set(random.sample(RIDERS, 4))  # the story: 4 riders remit short
for pid, (final, due, dts, rider) in truth.items():
    if final != "delivered" or due == 0:
        continue
    if random.random() < 0.12:
        continue  # planted issue: delivered, cash never remitted
    amount = due
    if rider in skimmers and random.random() < 0.45:
        amount = round(due * random.uniform(0.55, 0.85), -1)
    rid += 1
    remits.append({"remittance_id": f"T{rid:05d}", "parcel_id": pid, "rider_id": rider,
                   "amount": messy_money(amount),
                   "remitted_at": (dts + timedelta(hours=random.randint(2, 8))).isoformat(sep=" ")})

# planted issue: 18 remittances against parcels that were never delivered
for pid in random.sample([p for p, t in truth.items() if t[0] != "delivered"], 18):
    rid += 1
    remits.append({"remittance_id": f"T{rid:05d}", "parcel_id": pid, "rider_id": truth[pid][3],
                   "amount": messy_money(round(random.uniform(500, 9000), -1)),
                   "remitted_at": (START + timedelta(days=random.randint(2, 28))).isoformat(sep=" ")})

random.shuffle(scans)
random.shuffle(remits)
OUT.mkdir(exist_ok=True)
for name, rows in [("parcels", parcels), ("scans", scans), ("cod_remittances", remits)]:
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}.csv: {len(rows)} rows")

if "--check" in sys.argv:
    ids = [p["parcel_id"] for p in parcels]
    assert len(ids) - len(set(ids)) == 40, "duplicate parcels missing"
    assert any(s["parcel_id"] not in truth for s in scans), "orphan scans missing"
    assert len({s["zone"].strip() for s in parcels}) > len(ZONES) or any(
        p["zone"] != p["zone"].strip() for p in parcels), "zone casing/spacing clean"
    assert len({p["booked_date"][:4] for p in parcels}) > 1 or any(
        "/" in p["booked_date"] for p in parcels), "date formats uniform"
    assert any("Rs" in r["amount"] for r in remits), "money not messy"
    assert any(truth[r["parcel_id"]][0] != "delivered" for r in remits), "bad remittances missing"
    paid = {r["parcel_id"] for r in remits}
    assert any(t[0] == "delivered" and t[1] > 0 and p not in paid for p, t in truth.items()), "missing-cash case absent"
    print("checks passed")
