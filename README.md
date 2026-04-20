# MyFortress - Auxiliary Service Gateway

MyFortress is a subproject within the Aaroneous Automation Suite (AAS) ecosystem, functioning as an **auxiliary service gateway**. It provides a service layer consumed by AAS plugins and other components for various functionalities, and is typically included in the full workspace as a git submodule.

## Canonical Docs

The canonical documentation lives in the AAS superproject:

- Start here: https://github.com/Aarogaming/AaroneousAutomationSuite/blob/master/docs/START_HERE.md
- Docs index: https://github.com/Aarogaming/AaroneousAutomationSuite/blob/master/docs/INDEX.md
- Gate governance pointer: `docs/GATE_GOVERNANCE_POINTER.md`

## Key Changes & Integration Notes:

*   **AAS Configuration Files Relocated:** Core AAS configuration files (e.g., `aas-hive.json`, `aas-module.json`, `aas-plugin.json`) previously found at the root of this repository have been moved to the `AaroneousAutomationSuite` orchestrator's root directory (`D:/AaroneousAutomationSuite/`). MyFortress now consumes these configurations from the central orchestrator.
*   **Client File Renamed:** The client file previously known as `gateway/clients/aas.py` has been renamed to `gateway/clients/myfortress_client_for_aas_plugins.py` to better reflect its purpose: providing MyFortress services to AAS plugins.

## Repo Map

- `gateway/`: API + integrations, including client definitions for AAS plugins to interact with MyFortress services.
- `plugins/`: Plugin modules
- `tests/`: Test suite
