x = 10, 15 and 20 identical for every order: True

### What actually happened
| Order | Placed | Invoiced | Shipped by | Actual days | Real promise | Real result |
|---|---|---|---|---|---|---|
| 55577932 | 21 Sep 10:24 | 21 Sep 12:23 | 195 | 6 | 2 | Late |
| 55582558 | 21 Sep 12:00 | 22 Sep 12:13 | 195 | 2 | 2 | On-Time |
| 55417033 | 21 Sep 12:33 | 22 Sep 11:43 | 195 | 2 | 2 | On-Time |
| 55590586 | 21 Sep 13:57 | 21 Sep 15:41 | 195 | 3 | 2 | Late |
| 55490611 | 21 Sep 14:05 | 21 Sep 14:51 | 195 | 3 | 2 | Late |
| 55607286 | 21 Sep 18:30 | 22 Sep 11:09 | 195 | 2 | 2 | On-Time |
| 55615123 | 21 Sep 20:23 | 22 Sep 12:37 | 195 | 2 | 2 | On-Time |
| 55615163 | 21 Sep 20:24 | 23 Sep 11:26 | 246 | 3 | 2 | Late |
| 55626378 | 21 Sep 23:11 | 22 Sep 13:47 | 195 | 2 | 2 | On-Time |

### Today's rule (x = 1) and the new rule (x = 10, 15, 20)
| Order | Shipped by | Today: winner at placed / invoice | Today: A | Today: B | New: winner at placed / invoice | New: promise | New: A | New: B |
|---|---|---|---|---|---|---|---|---|
| 55577932 | 195 | 195 / 195 | 2d, +4, Late | Late | 246 / 246 | 2d | 3d, +3, Late | excluded |
| 55582558 | 195 | 195 / 195 | 2d, +0, On-Time | On-Time | 246 / 246 | 2d | 3d, -1, Early | excluded |
| 55417033 | 195 | 195 / 195 | 2d, +0, On-Time | On-Time | 246 / 246 | 2d | 3d, -1, Early | excluded |
| 55590586 | 195 | 195 / 195 | 2d, +1, Late | Late | 246 / 246 | 2d | 3d, +0, On-Time | excluded |
| 55490611 | 195 | 195 / 195 | 2d, +1, Late | Late | 246 / 246 | 2d | 3d, +0, On-Time | excluded |
| 55607286 | 195 | 195 / 195 | 2d, +0, On-Time | On-Time | 246 / 246 | 2d | 3d, -1, Early | excluded |
| 55615123 | 195 | 195 / 195 | 2d, +0, On-Time | On-Time | 246 / 246 | 2d | 3d, -1, Early | excluded |
| 55615163 | 246 | 195 / 225 | 2d, +1, Late | excluded | 246 / 246 | 2d | 2d, +1, Late | Late |
| 55626378 | 195 | 195 / 195 | 2d, +0, On-Time | On-Time | 246 / 246 | 2d | 3d, -1, Early | excluded |
