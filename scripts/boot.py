#!/usr/bin/env python3
"""
Standard AAS Microkernel Bootstrapper Template.
Drop this file into `YourRepoName/scripts/boot.py` and run it.
It automatically infers its repository name from the folder it lives in.
"""
import sys
import asyncio
from pathlib import Path

# Resolve the absolute path of the Federation root (D:\ or whatever it is called)
AAS_ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_SCRIPTS = AAS_ROOT / "Workbench" / "scripts"

# Inject the Universal Microkernel
sys.path.append(str(WORKBENCH_SCRIPTS))
sys.path.append(str(AAS_ROOT))

try:
    from aas_kernel import AASKernel
except ImportError:
    print(f"CRITICAL ERROR: Failed to import Universal AASKernel from Workbench. Is Workbench present at {WORKBENCH_SCRIPTS}?")
    sys.exit(1)

async def main():
    # Automatically determine our identity based on our folder name
    repo_root = Path(__file__).resolve().parents[1]
    repo_name = repo_root.name
    plugin_dir = repo_root / "plugins"

    print(f"--- INITIATING {repo_name.upper()} BOOT SEQUENCE ---")
    
    # Initialize the Microkernel with our dynamically discovered identity
    kernel = AASKernel(repo_name=repo_name, repo_root=str(repo_root))
    kernel.load_plugins_from_directory(str(plugin_dir))
    
    # Ignite NATS, Logging, Heartbeat, and Plugins
    await kernel.ignite()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"Kernel Shutdown.")
