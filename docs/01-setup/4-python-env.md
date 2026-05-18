# 4. Python environment

The scripts are stdlib + `azure-cosmos` + `pydantic` + `python-dotenv`.
No web framework.

```powershell
# from the repo root
python -m venv .venv
.venv\Scripts\Activate.ps1          # PowerShell
# .venv/bin/activate                # bash / zsh

pip install -r src/requirements.txt
```

Validate:

```powershell
python -c "import azure.cosmos, pydantic, dotenv; print('ok')"
```

## Cosmos connection settings (`.env`)

Every Python entry point loads `src/.env` via `python-dotenv` before it
constructs the `CosmosClient`. Copy the example file once:

```powershell
# PowerShell
Copy-Item src/.env.example src/.env

# bash / zsh
cp src/.env.example src/.env
```

The defaults in `.env.example` already point at the local Cosmos DB
emulator with its well-known public key, so on a stock setup you can
copy and move on. Edit `src/.env` only if you need a different profile
(Linux vNext preview emulator, real Azure Cosmos DB account, custom
database name). The file is gitignored — never commit it.

Recognised variables:

| Variable          | Default in `.env.example`        | Notes                                                  |
|-------------------|----------------------------------|--------------------------------------------------------|
| `COSMOS_ENDPOINT` | `https://localhost:8081`         | Required. Set to your account URL for Azure.           |
| `COSMOS_KEY`      | emulator well-known key          | Required. Replace with a real key for Azure.           |
| `COSMOS_DB`       | per-iteration default            | Optional override. Each iteration defaults to its own DB so you can run them side-by-side in one account (`Build26DEM310DB-i1a`, `-i1b`, `-i2`, `-i3`, `-i4`). |

If `COSMOS_ENDPOINT` or `COSMOS_KEY` is missing, the scripts raise a
clear error telling you to copy `.env.example` first.

You're ready to run the walkthrough.
