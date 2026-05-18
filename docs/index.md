# DEM310 walkthrough

The pages in this folder are the at-home companion to the session — the
material you'd need to reproduce the demo end-to-end on your own machine.

## Table of contents

1. **Setup** — [`01-setup/`](./01-setup/)
   - [Prerequisites](./01-setup/1-prerequisites.md)
   - [Cosmos DB emulator](./01-setup/2-cosmos-emulator.md)
   - [VS Code + Cosmos DB Agent](./01-setup/3-vscode-agent.md)
   - [Python environment](./01-setup/4-python-env.md)
2. **Scenario** — [`02-scenario/`](./02-scenario/)
   - [Business context](./02-scenario/1-business-context.md)
   - [Access patterns](./02-scenario/2-access-patterns.md)
   - [Volumetrics](./02-scenario/3-volumetrics.md)
3. **Walkthrough** — [`03-walkthrough/`](./03-walkthrough/)
   - [Iteration 1 — Naive port](./03-walkthrough/1-iteration-01-naive.md)
   - [Iteration 2 — Agent-guided redesign](./03-walkthrough/2-iteration-02-optimized.md)
   - [Iteration 3 — Composite indexes (optional)](./03-walkthrough/3-iteration-03-composite-indexes.md)
   - [Iteration 4 — Hybrid + vector search (optional, cloud-only)](./03-walkthrough/4-iteration-04-hybrid-vector-search.md)
4. **Takeaways** — [`04-takeaways.md`](./04-takeaways.md)

## Reference templates

The originals — useful when you adapt this demo to your own domain:

- [`access-patterns-template.md`](./access-patterns-template.md)
- [`volumetrics-template.md`](./volumetrics-template.md)
