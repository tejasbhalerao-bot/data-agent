# Serviceability — System Description (source snapshot)

Source: Tejas's Serviceability Google Doc, read 2026-06-18. Captured here so the gap analysis is self-contained. This is the system-of-record description; the gap catalog (`insights/2026-06-18-serviceability-instrumentation-gaps-v1.md`) is derived first-principles from it.

---

## What questions does Serviceability answer?

1. Which delivery location (pincode) is serviceable by Truemeds?
2. Which source location (warehouse) must the pincode be serviced from, preferentially?
3. Which delivery partner must be preferentially chosen to service that source × destination combination?

---

## Choosing Pincode and Warehouse

Business team uploads configuration on these parameters:

| Parameter | Implication |
|---|---|
| Pincode | Delivery pincode of the customer |
| Warehouse | Source from where the customer must be serviced |
| Priority | Order in which this warehouse is considered for this pincode |
| Is_serviceable | Whether this pincode × warehouse combination will be serviced by Truemeds |
| Is_sdd | Whether this pincode × warehouse combination is serviceable through the hyperlocal construct |
| Is_Cold_Chain_Deliverable | Whether this pincode × warehouse combination can service cold-chain orders |
| Active | Whether this uploaded configuration is currently active |

Stored in two tables:
- **`pincode_warehouse_master`** — for Fulfilment Centres (FCs)
- **`pincode_microfc_master`** — for Micro Fulfilment Centres (MFCs)

**Cart page:** defaults to the FC catalog → serviceability always determined by `pincode_warehouse_master`.

**Summary page:** runs an inventory check on the **priority-1 warehouse** from both `pincode_warehouse_master` (FC) and `pincode_microfc_master` (MFC). Conditional logic:
- Both MFC and FC have inventory → select **MFC**.
- MFC has no inventory, FC has → select **FC**.
- Both MFC and FC have no inventory → select **FC** (FCs are assumed to always have inventory via Just-In-Time procurement).

**Non-serviceable pincode handling:** the customer is **not** shown as non-serviceable upfront. The system defaults to the **Mumbai FC catalog** so the customer can browse — but **blocks the customer from placing an order** to this pincode.

---

## Choosing the delivery partner

First the system decides the **delivery construct**: Hyperlocal or Courier.
- **Hyperlocal** considers only 3 active couriers: **Ithink, Shipsy, Shiprocket**.
- All other active couriers fall under **Courier** by default.

Construct is decided by the **`is_sdd` flag** in `pincode_warehouse_master` / `pincode_microfc_master`: `is_sdd = True` → Hyperlocal; else → Courier.

### Hyperlocal construct — partner selection
Uses table **`sdd_pincode_mapping`**:

| Parameter | Implication |
|---|---|
| Warehouse | Source from where the customer must be serviced |
| Pincode | Delivery pincode of the customer |
| Delivery Partner | Partner that can be chosen for this pincode × warehouse combination |
| Priority | Order in which this partner is considered |
| Active | Whether this uploaded configuration is currently active |

**Anything beyond priority 1 is currently meaningless** — the system has no trigger to identify when to go beyond priority 1, so it always chooses the priority-1 courier. That priority-1 courier always services the order.

### Courier construct — partner selection
This selection logic lives in **Clickpost**, not in Truemeds' system (detailed in the Allocation document).

Within Clickpost, the team records which courier can service which pincode, for both **delivery** and **pickup**. This pincode-level info is maintained by the business team uploading a **CSV of eligible pincodes**.

**Exception — Bluedart:** configured with **"Automatic Fetch"** on Clickpost. When Bluedart updates its serviceable pincodes, we incorporate it immediately (synced via Clickpost) instead of discovering it late.

**All other couriers:** no Automatic Fetch. Serviceability is updated **only when the courier partner manually shares the serviceable-pincodes file with the ops team.**
