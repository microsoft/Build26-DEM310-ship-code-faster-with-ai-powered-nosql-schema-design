# naive-b — unbounded-array anti-pattern

**Anti-pattern under test:** keep one document per customer in a single
container; embed *every* order the customer ever places inside a growing
`orders[]` array on that document. Each new order is a read-modify-write
upsert of the whole document.

This is intuitive ("a customer has many orders → put them on the
customer") and **wrong**. It runs into three concrete problems:

1. **Write RU grows with the doc** — every upsert rewrites the entire
   document and reindexes the full array. RU for the upsert grows roughly
   linearly with the number of orders already on the doc.
2. **Read RU grows with the doc** — even fetching the customer's name
   pulls back every order ever placed.
3. **The 2 MB item limit is a hard ceiling.** Cosmos DB will reject an
   upsert that pushes the document over 2 MB with a 413 error. There is
   no graceful degradation — the customer can't place an order anymore.

## What `simulate.py` does

Picks one customer (`C00005` by default), then for **20 iterations**:

1. Reads the current customer doc and prints its size.
2. Appends one new order (with 1–10 line items copied from the master
   catalog) to the `orders[]` array.
3. Upserts the document and captures the upsert's RU charge.

At the end it prints a table — iteration, document size in KB, upsert RU
— and a projection of how many more iterations the doc has before it
crosses the 2 MB ceiling.

## Run it

```powershell
cd src/iteration-01-naive/naive-b
python complete/seed.py        # creates the container and seeds 10 customers with empty orders
python complete/simulate.py    # runs the 20-iteration growth simulation
```

To make the growth more dramatic in a 23-minute demo slot, bump the line
counts per order:

```powershell
python complete/simulate.py --iterations 20 --items-per-order 10
```

## What attendees should walk away with

- "Put many-of inside the one-of" feels right and is the single most
  expensive mistake to fix later.
- Both **write** and **read** RU grow with the size of the embedded
  array — not just storage cost.
- The 2 MB item limit will end the conversation eventually. The right
  question isn't "how do I shrink the array?", it's "should this array
  exist on this document at all?"

The answer in iteration 2: split the array into separate documents that
share the partition key.
