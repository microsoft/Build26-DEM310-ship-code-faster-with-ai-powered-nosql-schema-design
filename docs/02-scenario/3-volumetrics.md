# 3. Volumetrics

Numbers used to size partitions, request units, and indexing. The demo
seeds a small slice of these volumes — but the agent's recommendations
are driven by the production projections.

| Entity                        | Production target | Demo seed |
|-------------------------------|-------------------|-----------|
| Customers                     | 10 M               | 10        |
| Categories                    | 100                | 5         |
| Products                      | 100 k              | 50        |
| Orders / customer / year      | 10–40             | 20        |
| Items / order                 | 1–100              | 1–10      |
| Read RPS (P1+P2)              | 3000 sustained     | n/a       |
| Write RPS (P3)                | 500 sustained     | n/a       |
| Retention                     | 7 years           | 7 years   |

These projections — alongside the [access patterns](./2-access-patterns.md)
— are what the Cosmos DB Agent Kit reasons over to propose the target
design during the walkthrough.
