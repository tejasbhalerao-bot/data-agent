import pandas as pd
import numpy as np

CSV = "archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv"

date_cols = [
    "digitised_delivery_promise", "digitised_dispatch_promise",
    "delivery_attempt_time", "pickup_time", "awb_sticker_printed_ts"
]

chunks = []
for chunk in pd.read_csv(CSV, chunksize=100_000, low_memory=False,
                         parse_dates=date_cols):
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)

print(f"Total orders loaded: {len(df):,}")

# Date-only versions
df["d_promise"]   = df["digitised_delivery_promise"].dt.normalize()
df["d_attempt"]   = df["delivery_attempt_time"].dt.normalize()
df["d_pickup"]    = df["pickup_time"].dt.normalize()
df["d_dig_disp"]  = df["digitised_dispatch_promise"].dt.normalize()

# --- Base population: orders with a delivery attempt ---
base = df[df["d_attempt"].notna()].copy()
print(f"\nOrders with delivery attempt: {len(base):,}")

# --- Q1: Late orders (delivery attempt > digitised promise) ---
q1 = base[base["d_attempt"] > base["d_promise"]].copy()
print(f"\nQ1 — Late orders (delivery > digitised promise): {len(q1):,}")
print(f"     % of delivery-attempted: {len(q1)/len(base)*100:.2f}%")

# --- Q2: Q1 orders where shipping courier was adherent to their own TAT ---
# actual_tat = d_attempt - d_pickup in days
# adherent to shipping promise = actual_tat <= shipping_delivery_promise
q2_base = q1[q1["d_pickup"].notna() & q1["shipping_delivery_promise"].notna()].copy()
q2_base["actual_tat"] = (q2_base["d_attempt"] - q2_base["d_pickup"]).dt.days
q2 = q2_base[q2_base["actual_tat"] <= q2_base["shipping_delivery_promise"]].copy()

print(f"\nQ2 — Late but shipping courier was adherent to their own TAT: {len(q2):,}")
print(f"     % of Q1 (late orders):        {len(q2)/len(q1)*100:.2f}%")
print(f"     % of delivery-attempted base: {len(q2)/len(base)*100:.2f}%")

# --- Addressable within Q2 ---
# Digitised TAT in days: DATE(digitised_delivery_promise) - DATE(digitised_dispatch_promise)
q2["digitised_tat"] = (q2["d_promise"] - q2["d_dig_disp"]).dt.days

# Courier switched?
q2["courier_switched"] = (
    q2["digitised_delivery_partner"].notna() &
    q2["shipping_delivery_partner"].notna() &
    (q2["digitised_delivery_partner"] != q2["shipping_delivery_partner"])
)

# Switched to a slower courier (digitised TAT < shipping TAT)
q2["switched_to_slower"] = (
    q2["courier_switched"] &
    (q2["digitised_tat"] < q2["shipping_delivery_promise"])
)

switched_slower = q2[q2["switched_to_slower"]]
same_courier    = q2[~q2["courier_switched"]]
switched_faster_or_same = q2[q2["courier_switched"] & ~q2["switched_to_slower"]]

print(f"\n--- Q2 breakdown ---")
print(f"Courier unchanged (pipeline slipped, same courier too slow for budget): {len(same_courier):,}  ({len(same_courier)/len(q2)*100:.1f}% of Q2)")
print(f"Courier switched to slower (definitively addressable):                  {len(switched_slower):,}  ({len(switched_slower)/len(q2)*100:.1f}% of Q2)")
print(f"Courier switched to faster/same TAT (not addressable by reallocation):  {len(switched_faster_or_same):,}  ({len(switched_faster_or_same)/len(q2)*100:.1f}% of Q2)")

print(f"\n--- Impact summary ---")
print(f"Total delivery-attempted orders:         {len(base):,}")
print(f"Q1 — Late orders:                        {len(q1):,}  ({len(q1)/len(base)*100:.2f}%)")
print(f"Q2 — Courier-adherent lates (TAM):       {len(q2):,}  ({len(q2)/len(base)*100:.2f}%)")
print(f"     Definitively addressable (switched to slower): {len(switched_slower):,}  ({len(switched_slower)/len(base)*100:.2f}% of base)")
print(f"     Pipeline-slip same-courier (lower bound 0, upper bound addressable): {len(same_courier):,}  ({len(same_courier)/len(base)*100:.2f}% of base)")
print(f"\nConservative floor (switched to slower only):  {len(switched_slower)/len(base)*100:.2f}pp adherence uplift potential")
print(f"Full TAM ceiling (all Q2):                     {len(q2)/len(base)*100:.2f}pp adherence uplift potential")
