# AdventureWorksLT source data

These files are the raw inputs used by [`../generate.py`](../generate.py) to
produce the trimmed master JSON in [`../master/`](../master/).

| File                     | Purpose                                                       |
|--------------------------|---------------------------------------------------------------|
| `AdventureWorksLT.sql`   | Original `CREATE TABLE` definitions — useful for column types |
| `Customer.csv`           | Customer profile rows                                         |
| `Address.csv`            | Physical addresses                                            |
| `CustomerAddress.csv`    | Many-to-many between `Customer` and `Address`                 |
| `ProductCategory.csv`    | Product category hierarchy                                    |
| `Product.csv`            | Product catalog (includes binary thumbnail column — ignored)  |
| `SalesOrderHeader.csv`   | Sales order summary rows                                      |
| `SalesOrderDetail.csv`   | Sales order line items                                        |

## CSV format notes

- Field separator: comma.
- Decimal separator inside quoted numeric strings is a **comma** (European
  locale), e.g. `"1059,3100"` represents `1059.31`. The generator handles
  this when parsing.
- Date/time columns use `YYYY-MM-DD HH:MM:SS.fff`.

## Attribution

AdventureWorksLT is a Microsoft sample database originally published for
SQL Server. The CSV files here are an exported snapshot used for
demonstration purposes only. See the Microsoft sample databases page on
GitHub for the canonical source.
