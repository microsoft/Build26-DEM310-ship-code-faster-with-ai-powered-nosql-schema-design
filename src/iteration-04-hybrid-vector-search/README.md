# Iteration 4 — Hybrid + Vector Search (optional)

This iteration is **cloud-only**. The Cosmos DB local emulator (classic
Windows and Linux vNext preview) does not yet support the
[NoSQL Vector Search](https://learn.microsoft.com/azure/cosmos-db/nosql/vector-search)
or
[Full-Text Search](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)
capabilities the code below relies on. You will provision a small Azure
Cosmos DB account and an Azure AI Foundry / Azure OpenAI resource via
the included Bicep templates, then run the seed + search scripts against
them using **Entra ID + RBAC** — no account keys, no connection strings.

## What this iteration shows

Three additional access patterns on top of the iteration-02 product
catalog:

| ID | Pattern | Cosmos feature |
| --- | --- | --- |
| R-VEC-1 | "Find products similar to this description" | Vector search via `VectorDistance()` |
| R-FTS-1 | "Find products whose description matches these words" | Full-text search via `FullTextContains*` + `FullTextScore` |
| R-HYB-1 | "Best of both — relevance + semantic similarity" | Hybrid search via `ORDER BY RANK RRF(...)` |

See [`access-patterns.md`](./access-patterns.md) for the full
specification and target RU budgets.

## Layout

```text
iteration-04-hybrid-vector-search/
├── README.md
├── access-patterns.md
├── requirements.txt              # azure-identity + openai (in addition to /src/requirements.txt)
├── infra/
│   ├── README.md
│   ├── main.bicep                # resource-group-scope orchestrator
│   ├── main.bicepparam           # all parameters, defaults are demo-safe
│   ├── modules/
│   │   ├── cosmos.bicep          # Cosmos account + DB + container (vector + FTS policies)
│   │   ├── foundry.bicep         # AI Services account + chat + embedding deployments
│   │   └── rbac.bicep            # Cosmos Operator (control plane) + SQL Data Contributor
│   │                             #   (data plane) + Cognitive Services OpenAI User
│   └── deploy.ps1                # one-shot wrapper around `az deployment group create`
├── complete/                     # Entra-ID-authenticated, end-to-end
│   ├── shared.py                 #   DefaultAzureCredential + AAD CosmosClient + AzureOpenAI client
│   ├── seed.py                   #   generates embeddings, creates container, upserts
│   └── search.py                 #   vector, full-text, hybrid demos with RU + metrics
└── demo/                         # same shape with TODOs for you to fill in
    ├── shared.py
    ├── seed.py
    └── search.py
```

## One-time setup

1. **Sign in to Azure** with the identity you want the demo to run as
   (this same identity will be granted both control-plane and data-plane
   RBAC during deployment):

   ```powershell
   az login
   az account set --subscription <your-subscription-id>
   ```

2. **Provision the infra** (creates resource group, Cosmos DB account
   with vector + FTS capabilities enabled, AI Foundry account with two
   model deployments, and all required role assignments — see
   [`infra/README.md`](./infra/README.md) for details and parameters):

   ```powershell
   cd src/iteration-04-hybrid-vector-search/infra
   ./deploy.ps1 -ResourceGroup rg-dem310-i4 -Location eastus2
   ```

   The script prints the `cosmosEndpoint` and `foundryEndpoint` outputs.

3. **Update your `.env`** with the new variables (copy from
   [`/src/.env.example`](../.env.example), section *"Iteration 4 —
   cloud Cosmos DB + Azure AI Foundry"*) — pasting the two endpoint
   values is all you need; auth flows through `DefaultAzureCredential`.

4. **Install the extra Python dependencies** (into the same venv from
   [setup step 4](../../docs/01-setup/4-python-env.md)):

   ```powershell
   .venv\Scripts\Activate.ps1          # PowerShell
   # source .venv/bin/activate         # bash / zsh
   pip install -r src/iteration-04-hybrid-vector-search/requirements.txt
   ```

## Run

The runtime lives at the repo root (`scripts/seed_iteration_04.py` plus
the vec/fts/hyb commands on `demo/app/queries.py`) per
[CONVENTIONS.md](../../docs/03-walkthrough/CONVENTIONS.md).

```powershell
# from repo root
# Creates ProductsRich container, generates embeddings, upserts ~150 docs
python -u -m scripts.seed_iteration_04                                                       --log logs/iter-04/seed.log

# Runs the three search patterns and prints RU + x-ms-item-count
# + x-ms-documentdb-query-metrics for each.
python -u -m demo.app.queries vec "lightweight aluminum mountain bike for trails"           --log logs/iter-04/step5-vec.log
python -u -m demo.app.queries fts "helmet visor adjustable"                                 --log logs/iter-04/step5-fts.log
python -u -m demo.app.queries hyb "comfortable long-distance road bike saddle"              --log logs/iter-04/step5-hyb.log
```

The `src/iteration-04-hybrid-vector-search/{complete,demo}/` folders
are reference content only.

## Tear-down

The whole iteration lives in one resource group — delete it when you're
done:

```powershell
az group delete --name rg-dem310-i4 --yes --no-wait
```

## Notes & caveats

* **Cost.** This iteration provisions billable Azure resources. With
  default parameters (Cosmos serverless, AI Foundry S0, ~150 embeddings)
  a 30-minute demo costs well under USD 1, but you must remember to
  delete the resource group.
* **Region.** Vector + FTS + the listed model SKUs are not available in
  every region. The default `eastus2` is a safe pick at time of writing
  — pick another from
  [the model availability matrix](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)
  if needed.
* **Keys are off.** Both the Cosmos account and the Foundry account are
  provisioned with `disableLocalAuth: true`. All access is Entra-ID-only.
* This iteration is **independent** of iterations 1–3 — it does not
  read from or write to the emulator-based databases.
