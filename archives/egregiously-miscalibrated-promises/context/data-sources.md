# Data Sources — Egregiously Miscalibrated Promises

| File | Description | Location |
|------|-------------|----------|
| `all-orders-july-2026.csv` | All July 2026 orders with promise inputs (at digitization), actuals, and shipping state. ~804K rows, 42 columns. | `raw-data/all-orders-july-2026.csv` (local only, gitignored) · [Google Drive](https://drive.google.com/file/d/1qu_zpxGB8bYo5u6sGCvfz_kQGmiD0E50/view?usp=sharing) |

---

## `all-orders-july-2026.csv` — Column Reference

**Coverage:** July 2026 orders. One row per order.

### Order lifecycle timestamps

| # | Column | Description |
|---|--------|-------------|
| 1 | `order_id` | Unique identifier for the order |
| 2 | `digitised_ts` | Time when the order was placed |
| 3 | `dr_confirm_ts` | Time when doctor confirmed the order |
| 4 | `invoice_create_ts` | Time when the invoice was created for the order |
| 5 | `processing_start_ts` | Time when warehouse was ready to start processing the order |

### Promises at order placement (`digitised_*`)

State of the promise engine **at the time the order was placed** — inputs and outputs used to compute what was shown to the customer.

| # | Column | Description |
|---|--------|-------------|
| 6 | `digitised_dr_promise` | Time when the doctor call was promised to happen |
| 7 | `digitised_wh_promise` | Time when the warehouse promised to complete packing the order |
| 8 | `digitised_dispatch_promise` | Time when the courier promised to pick up the order |
| 9 | `digitised_delivery_promise` | Time when the courier promised to deliver the order |
| 10 | `digitised_wh_process_mins` | Time in minutes the warehouse promised to pack the order (within WH working hours) |
| 11 | `digitised_delivery_tat_mins` | Time in minutes the courier promised to take to deliver the order |
| 12 | `digitised_doctor_tat` | Time in minutes within which the doctor promised to call the customer after order placed |
| 13 | `digitised_dispatch_tat` | Time in minutes within which the courier promised to pick up the order after WH promised to finish packing |
| 14 | `digitised_is_sdd` | SDD serviceability state of the order when it was placed |
| 15 | `digitised_is_inventory` | Inventory state of the order when it was placed |
| 16 | `digitised_wh_id` | Warehouse the order was assigned to after it was placed |
| 17 | `digitised_order_category` | Category in which the order was computed after it got placed |
| 18 | `digitised_is_mfc` | Whether the warehouse assigned at order placement was MFC or FC |
| 19 | `digitised_delivery_pincode` | Pincode to which the customer requested delivery when the order was placed |
| 20 | `digitised_delivery_partner` | Delivery partner the system selected to deliver the order when it was placed |

### Working hours at order placement

| # | Column | Description |
|---|--------|-------------|
| 21 | `doctor_work_start` | Hour of day when the doctor starts work |
| 22 | `doctor_work_end` | Hour of day when the doctor ends work |
| 23 | `wh_processing_type` | Type of order the warehouse has to process |
| 24 | `warehouse_work_start` | Hour of day when the warehouse opens and begins work |
| 25 | `warehouse_work_end` | Hour of day when the warehouse closes and ends work |

### Payment

| # | Column | Description |
|---|--------|-------------|
| 26 | `initial_payment_type` | Payment method selected by the customer when the order was placed |
| 27 | `final_payment_code` | (Enum) Payment method finally recorded when the order was shipped / at customer's doorstep |
| 28 | `final_payment_type` | Payment method finally recorded when the order was shipped / at customer's doorstep |

### Actuals

| # | Column | Description |
|---|--------|-------------|
| 29 | `actual_doctor_call_time` | Time when the doctor made the first attempt to call the customer |
| 30 | `actual_warehouse_processing` | Time when the warehouse actually finished processing the order |
| 31 | `awb_sticker_printed_ts` | Time when the warehouse printed the AWB label on the box |
| 32 | `payment_pending_ts` | Time when the order entered payment pending state. NULL if it never entered |
| 33 | `payment_completed_ts` | Time when the customer completed payment |
| 34 | `pickup_time` | Time when the courier actually picked up the order from the warehouse |
| 35 | `delivery_attempt_time` | Time when the courier made the 1st delivery attempt to the customer |
| 36 | `actual_delivery_date` | Time when the order was actually delivered to the customer |

### State at shipping (`shipping_*`)

State of the order **at time of actual shipping** — may differ from `digitised_*` if order was rerouted or reassigned.

| # | Column | Description |
|---|--------|-------------|
| 37 | `shipping_pincode` | Pincode to which delivery was actually attempted |
| 38 | `shipping_delivery_partner` | Delivery partner who actually shipped the order |
| 39 | `shipping_delivery_promise` | Promise TAT in **days** (pickup → delivery attempt) of the courier who actually shipped the order |
| 40 | `shipping_warehouse` | Warehouse from which the order was actually shipped |
| 41 | `shipping_is_sdd` | SDD serviceability state of the order when it was shipped |
| 42 | `shipping_is_inventory` | Inventory state of the order when it was actually shipped |

---

## Notes

- `digitised_*` = promise engine state at order placement = what the customer was shown
- `shipping_*` = actual state at dispatch = what the courier received
- `digitised_wh_id` vs `shipping_warehouse` divergence → order was rerouted between placement and dispatch
- `delivery_attempt_time` is NULL for orders not yet attempted or not yet shipped
- File is 365MB / ~804K rows — load with chunked reads or filtering in scripts
