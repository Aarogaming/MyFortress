import asyncio
import sys
import logging
import json
import os
import aiohttp
from pathlib import Path
import ast

# Add Library Core to path
sys.path.append(str(Path(r"D:\Library\Core")))
from run_agent import AASAgent

logger = logging.getLogger("AAS.SentinelEngine")

def vet_code(file_path: str) -> str:
    """
    Simulates The Crucible. 
    Reads the file, checks syntax, and looks for basic issues.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Crucible Error: The file {file_path} was not found."

        source = path.read_text(encoding="utf-8")
        
        # 1. Syntax Check
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return f"CRITICAL REJECTION: The Crucible detected a SyntaxError on line {e.lineno}: {e.msg}"

        # 2. Simple Static Analysis (Look for risky imports)
        forbidden_modules = ["os", "subprocess", "sys"]
        found_risks = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_modules:
                        found_risks.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module in forbidden_modules:
                    found_risks.append(node.module)

        if found_risks:
            return f"CRITICAL REJECTION: The Crucible detected unauthorized modules ({', '.join(found_risks)}). Hephaestus must remove them."

        # Pass
        logger.info(f"Crucible passed for {file_path}")
        return f"CRUCIBLE APPROVED: {file_path} is syntactically sound and contains no explicitly forbidden imports. The Sentinel clears this artifact."

    except Exception as e:
        return f"Crucible Error: An unexpected exception occurred during vetting: {e}"

async def main():
    argus = AASAgent(
        repo_name="MyFortress", 
        persona_name="Argus", 
        system_prompt_path=str(Path(r"D:\MyFortress\.aas\AGENTS.md")),
        allow_tier_3=False # Keep security operations strictly local, except for explicit tools like audit_secrets
    )

    argus.register_tool(
        name="vet_code",
        func=vet_code,
        description="The Crucible's static analysis engine. Provide a full absolute file path (e.g., D:\\Workbench\\artifacts\\test.py). It will parse the file and return approval or rejection reasons based on syntax and secure coding practices.",
        schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "The absolute path to the python script to vet."}
            },
            "required": ["file_path"]
        }
    )

    def audit_vault_secrets() -> str:
        """Runs the vault_auditor to check the health and capabilities of our API keys."""
        import subprocess
        script_path = Path(r"D:\MyFortress\scripts\audit_secrets.py")
        if not script_path.exists():
            return "Crucible Error: Auditor script missing."
        
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        return result.stdout

    argus.register_tool(
        name="audit_vault_secrets",
        func=audit_vault_secrets,
        description="Audits The Vault (.env) to test the validity of API keys (GitHub, OpenAI, Gemini) and generates an inventory report of what capabilities the federation has access to.",
        schema={
            "type": "object",
            "properties": {}
        }
    )

    def ingest_external_env(env_path: str) -> str:
        """Reads an external .env file, normalizes the keys, and securely merges them into The Vault."""
        try:
            path = Path(env_path)
            if not path.exists() or not path.is_file():
                return f"Error: No valid file found at {env_path}"
                
            KEY_MAP = {
                "OPENAI_KEY": "OPENAI_API_KEY",
                "GEMINI_KEY": "GEMINI_API_KEY",
                "GOOGLE_API_KEY": "GEMINI_API_KEY",
                "GITHUB_TOKEN": "GITHUB_PAT",
                "ANTHROPIC_KEY": "ANTHROPIC_API_KEY",
                "AWS_KEY": "AWS_ACCESS_KEY_ID",
                "AWS_SECRET": "AWS_SECRET_ACCESS_KEY"
            }
            
            vault_env = Path(r"D:\MyFortress\.env")
            if not vault_env.exists():
                vault_env.parent.mkdir(parents=True, exist_ok=True)
                vault_env.write_text("# MyFortress Vault\n", encoding="utf-8")
                
            lines = vault_env.read_text(encoding="utf-8").splitlines()
            updates = {}
            
            # Parse external file
            for line in path.read_text(encoding="utf-8").splitlines():
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip().upper()
                    v = v.strip().strip('"').strip("'")
                    normalized_key = KEY_MAP.get(k, k)
                    updates[normalized_key] = v
                    
            if not updates:
                return "No valid key-value pairs found in the provided file."
                
            # Merge updates
            for key_name, new_val in updates.items():
                found = False
                for i, vault_line in enumerate(lines):
                    if vault_line.startswith(f"{key_name}="):
                        lines[i] = f'{key_name}="{new_val}"'
                        found = True
                        break
                if not found:
                    lines.append(f'{key_name}="{new_val}"')
                    
            vault_env.write_text("\n".join(lines) + "\n", encoding="utf-8")
            
            # Immediately trigger an audit to verify the newly ingested keys
            audit_results = audit_vault_secrets()
            return f"Successfully ingested and normalized {len(updates)} secrets into The Vault.\n\nPost-Ingestion Audit:\n{audit_results}"
            
        except Exception as e:
            return f"Error ingesting .env file: {str(e)}"

    argus.register_tool(
        name="ingest_external_env",
        func=ingest_external_env,
        description="Reads an external .env file, normalizes common API key names to the AAS standard, and securely merges them into The Vault (D:\\MyFortress\\.env). Automatically runs a Vault Audit afterward to verify the new keys.",
        schema={
            "type": "object",
            "properties": {
                "env_path": {
                    "type": "string",
                    "description": "The absolute path to the external .env file to ingest."
                }
            },
            "required": ["env_path"]
        }
    )

    async def automated_audit_loop():
        """A background process that runs the vault audit regularly and announces critical changes."""
        await asyncio.sleep(5) # Wait for agent to fully boot
        while True:
            logger.info("[Argus] Running automated routine Vault Audit...")
            report = audit_vault_secrets()
            
            # Briefly summarize the report to keep the broadcast concise
            # Only announce if there is an issue or simply state "Vault Audit Complete"
            if "Inactive" in report or "Missing" in report:
                alert = f"[Vault Alert] Routine audit detected missing or inactive keys. See Vault Inventory for details."
            else:
                alert = f"[Vault Audit] Routine audit complete. All federation keys are currently Active."
                
            try:
                # Use the global broadcast tool we built in run_agent.py
                await argus._broadcast_global(alert)
            except Exception as e:
                logger.error(f"Failed to broadcast audit results: {e}")
                
            # Sleep for 60 minutes (3600 seconds) before the next automated audit
            await asyncio.sleep(3600)

    async def oracle_heartbeat():
        """
        Background process that silently pings the Cloud API endpoints to read rate limit headers.
        Updates the Omni Ephemeral State with the current supply of Cloud Reserves.
        """
        await asyncio.sleep(10) # Let the system boot up first
        
        while True:
            try:
                reserves = {
                    "provider": "unknown",
                    "status": "offline",
                    "remaining_requests": "unknown",
                    "remaining_tokens": "unknown",
                    "reset_time": "unknown",
                    "last_checked": "never"
                }

                # Check which key we have. Prefer OpenAI for the standardized headers.
                openai_key = os.getenv("OPENAI_API_KEY")
                gemini_key = os.getenv("GEMINI_API_KEY")
                
                if openai_key:
                    reserves["provider"] = "openai"
                    url = "https://api.openai.com/v1/models"
                    headers = {"Authorization": f"Bearer {openai_key}"}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=5) as response:
                            if response.status == 200:
                                reserves["status"] = "online"
                                # OpenAI Rate Limit Headers
                                reserves["remaining_requests"] = response.headers.get("x-ratelimit-remaining-requests", "unlimited")
                                reserves["remaining_tokens"] = response.headers.get("x-ratelimit-remaining-tokens", "unlimited")
                                reserves["reset_time"] = response.headers.get("x-ratelimit-reset-tokens", "unknown")
                            elif response.status == 401:
                                reserves["status"] = "invalid_key"
                            else:
                                reserves["status"] = f"error_{response.status}"
                
                elif gemini_key:
                    reserves["provider"] = "gemini"
                    # Google's OpenAI-compatible endpoint
                    url = "https://generativelanguage.googleapis.com/v1beta/openai/models"
                    headers = {"Authorization": f"Bearer {gemini_key}"}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=5) as response:
                            if response.status == 200:
                                reserves["status"] = "online"
                                # Note: Gemini might not provide the exact same headers, but we record success
                            elif response.status == 401:
                                reserves["status"] = "invalid_key"
                            else:
                                reserves["status"] = f"error_{response.status}"
                else:
                    reserves["status"] = "no_keys_in_vault"

                import datetime
                reserves["last_checked"] = datetime.datetime.utcnow().isoformat()

                # Send the metrics straight to Library (Dionysus) via Instinct Router to update Omni
                payload = {
                    "key": "cloud_reserves",
                    "value_json": json.dumps(reserves)
                }
                
                await argus._send_direct_message("Library", f"/call update_ephemeral_state {json.dumps(payload)}")
                
            except Exception as e:
                logger.error(f"[Oracle Heartbeat] Failed to ping API reserves: {e}")

            # Sleep for 60 seconds to avoid spamming the APIs
            await asyncio.sleep(60)

    # Start the background loops
    asyncio.create_task(automated_audit_loop())
    asyncio.create_task(oracle_heartbeat())

    await argus.start()

if __name__ == "__main__":
    asyncio.run(main())
