# 4. Python environment

The scripts are stdlib + `azure-cosmos` + `pydantic`. No web framework.

```powershell
# from the repo root
python -m venv .venv
.venv\Scripts\Activate.ps1          # PowerShell
# .venv/bin/activate                # bash / zsh

pip install -r src/requirements.txt
```

Validate:

```powershell
python -c "import azure.cosmos, pydantic; print('ok')"
```

Optional environment overrides (defaults are the well-known emulator):

```powershell
$env:COSMOS_ENDPOINT = "https://localhost:8081"
$env:COSMOS_KEY      = "<emulator key>"
$env:COSMOS_DB       = "Build26DEM310"
```

You're ready to run the walkthrough.
