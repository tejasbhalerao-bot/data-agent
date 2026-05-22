# Data Sources — pba-integration

| File | Description | Location |
|------|-------------|----------|
| 2026-05-12-cutoff-times.csv | Pickup cutoff times per warehouse × courier. Rows = warehouses (city + pincode), columns = courier-mode combinations. Blank = courier not configured at that warehouse. | `context/2026-05-12-cutoff-times.csv` |
| 2026-05-22-courier-pricing-snapshot.md | Per-shipment pricing configured in Clickpost for each courier. Pricing mismatch → order on default pricing. Shiprocket and Shadowfax excluded from analysis scope. | `context/2026-05-22-courier-pricing-snapshot.md` |
