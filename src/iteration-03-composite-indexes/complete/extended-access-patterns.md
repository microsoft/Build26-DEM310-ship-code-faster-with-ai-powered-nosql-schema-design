# Extended access patterns (iteration 3)

These are the three queries that show up in production telemetry once
iteration 2 is live. Each one keeps the iteration-2 container layout but
needs a composite index to avoid a `ORDER BY`-on-multiple-fields penalty.

## R-EXT-1 — Customer order history by date range

> "Show me everything customer C00005 ordered in Q1 2026, most recent first."

```sql
SELECT * FROM c
WHERE  c.type = 'order'
  AND  c.customerId = @cid
  AND  c.orderDate >= @from
  AND  c.orderDate <  @to
ORDER  BY c.orderDate DESC
```

- Container: `CustomerOrders` (partition key `/customerId`)
- Already in-partition (filter on `customerId`).
- `ORDER BY c.orderDate DESC` combined with the `c.type = 'order'` filter
  needs the composite index **`[type ASC, orderDate DESC]`**.

## R-EXT-2 — Open-orders dashboard

> "List every order in `Placed` status across the platform, most recent first."

```sql
SELECT c.orderId, c.customerId, c.orderDate, c.totalAmount
FROM   c
WHERE  c.type = 'order'
  AND  c.status = @status
ORDER  BY c.orderDate DESC
```

- Container: `CustomerOrders`
- This one **is** cross-partition (no `customerId` filter) — that's expected
  for an admin dashboard. The composite index **`[status ASC, orderDate DESC]`**
  removes the in-memory sort, which is what blows up RU on cross-partition.

## R-EXT-3 — Product browsing by rating + price

> "Show me the highest-rated products in CAT006; for ties show the cheapest first."

```sql
SELECT c.productId, c.name, c.rating, c.price
FROM   c
WHERE  c.categoryId = @cid
ORDER  BY c.rating DESC, c.price ASC
```

- Container: `Products` (partition key `/categoryId`)
- In-partition. The two-column `ORDER BY` requires the composite index
  **`[rating DESC, price ASC]`**.

## Putting it in the indexing policy

See [`indexing-policy.json`](./indexing-policy.json). The three composites
above are appended to the iteration-2 policy:

```jsonc
"compositeIndexes": [
  [{ "path": "/type",   "order": "ascending"  },
   { "path": "/orderDate", "order": "descending" }],

  [{ "path": "/status", "order": "ascending"  },
   { "path": "/orderDate", "order": "descending" }],

  [{ "path": "/rating", "order": "descending" },
   { "path": "/price",  "order": "ascending"  }]
]
```

The first two apply to `CustomerOrders`; the third to `Products`. The
provided `queries.py --apply-policy` splits the file accordingly.
