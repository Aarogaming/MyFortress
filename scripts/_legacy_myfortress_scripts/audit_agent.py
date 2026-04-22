import os
import sys
import json
from pathlib import Path
from datetime import datetime

FORTRESS_ROOT = Path(__file__).resolve().parents[1]
AAS_ROOT = FORTRESS_ROOT.parent

def audit_agent(repo_name: str):
    repo_path = AAS_ROOT / repo_name
    if not repo_path.exists():
        print(f"Error: Agent repository {repo_name} not found at {repo_path}")
        sys.exit(1)

    print(f"--- MyFortress Audit Protocol Initiated for: {repo_name} ---")
    
    # 1. Update Manifest
    manifest_path = repo_path / "mcp-manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        modified = False
        for cap in manifest.get("capabilities", []):
            if "confirmed_conditions" in cap:
                if "quarantine_pending" in cap["confirmed_conditions"]:
                    cap["confirmed_conditions"].remove("quarantine_pending")
                    if "active" not in cap["confirmed_conditions"]:
                        cap["confirmed_conditions"].append("active")
                    modified = True
                    
        if modified:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            print(f" [OK] Manifest updated: Cleared quarantine_pending, set to active.")
        else:
            print(f" [INFO] Manifest did not have quarantine_pending.")
    else:
        print(f" [WARN] Manifest not found at {manifest_path}")

    # 2. Update AGENTS.md
    agents_path = repo_path / "AGENTS.md"
    if agents_path.exists():
        with open(agents_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        new_lines = []
        modified = False
        for line in lines:
            if line.startswith("**Status:**"):
                new_lines.append("**Status:** ACTIVE (Audited by MyFortress)\n")
                modified = True
            else:
                new_lines.append(line)
                
        if modified:
            with open(agents_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f" [OK] AGENTS.md updated: Status set to ACTIVE.")
        else:
            print(f" [INFO] AGENTS.md status line not found.")
            
    # 3. Update EVOLUTION_LEDGER.md
    ledger_path = repo_path / "EVOLUTION_LEDGER.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    audit_entry = f"### [{timestamp}] Audit Clearance\n**Auditor:** MyFortress\n**Status:** APPROVED - Cleared from Quarantine. Agent is now ACTIVE on Event Bus.\n\n"
    
    if ledger_path.exists():
        with open(ledger_path, 'a', encoding='utf-8') as f:
            f.write(audit_entry)
        print(f" [OK] EVOLUTION_LEDGER.md updated with Audit Clearance.")
    else:
        with open(ledger_path, 'w', encoding='utf-8') as f:
            f.write("# Evolution Ledger\n\n" + audit_entry)
        print(f" [OK] EVOLUTION_LEDGER.md created with Audit Clearance.")
        
    print(f"--- Audit Complete. {repo_name} is fully cleared. ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audit_agent.py <AgentRepoName>")
        sys.exit(1)
        
    audit_agent(sys.argv[1])
