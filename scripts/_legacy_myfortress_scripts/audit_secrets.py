import asyncio
import aiohttp
import json
from pathlib import Path

ENV_PATH = Path(r"D:\MyFortress\.env")
INVENTORY_PATH = Path(r"D:\MyFortress\artifacts\vault_inventory.json")

async def check_github(session, token):
    if not token: return {"status": "Missing", "capabilities": []}
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        async with session.get("https://api.github.com/rate_limit", headers=headers, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                core_limit = data.get("resources", {}).get("core", {})
                return {
                    "status": "Active",
                    "capabilities": ["Source Control", "CI/CD Workflows", "Repo Management"],
                    "remaining_requests": core_limit.get("remaining"),
                    "reset_time": core_limit.get("reset")
                }
            else:
                return {"status": f"Inactive (HTTP {resp.status})", "capabilities": []}
    except Exception as e:
        return {"status": f"Error: {e}", "capabilities": []}

async def check_openai(session, token):
    if not token: return {"status": "Missing", "capabilities": []}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get("https://api.openai.com/v1/models", headers=headers, timeout=10) as resp:
            if resp.status == 200:
                return {
                    "status": "Active",
                    "capabilities": ["Tier 3 LLM Generation", "Embeddings", "Vision"]
                }
            else:
                text = await resp.text()
                return {"status": f"Inactive (HTTP {resp.status})", "details": text[:100], "capabilities": []}
    except Exception as e:
        return {"status": f"Error: {e}", "capabilities": []}

async def check_gemini(session, token):
    if not token: return {"status": "Missing", "capabilities": []}
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={token}"
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                return {
                    "status": "Active",
                    "capabilities": ["Tier 3 LLM Generation", "Massive Context Window (1M-2M tokens)"]
                }
            else:
                text = await resp.text()
                return {"status": f"Inactive (HTTP {resp.status})", "details": text[:100], "capabilities": []}
    except Exception as e:
        return {"status": f"Error: {e}", "capabilities": []}

async def main():
    if not ENV_PATH.exists():
        print("Vault not found.")
        return

    secrets = {}
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                secrets[k.strip()] = v.strip().strip("'").strip('"')

    print("Auditing The Vault...")
    inventory = {}
    
    async with aiohttp.ClientSession() as session:
        # Check GitHub
        gh_token = secrets.get("GITHUB_PAT") or secrets.get("GITHUB_TOKEN")
        print("- Checking GitHub...")
        inventory["GitHub"] = await check_github(session, gh_token)
        
        # Check OpenAI
        oa_token = secrets.get("OPENAI_API_KEY")
        print("- Checking OpenAI...")
        inventory["OpenAI"] = await check_openai(session, oa_token)
        
        # Check Gemini
        gem_token = secrets.get("GEMINI_API_KEY")
        print("- Checking Gemini...")
        inventory["Gemini"] = await check_gemini(session, gem_token)

    INVENTORY_PATH.parent.mkdir(exist_ok=True)
    INVENTORY_PATH.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    
    print("\n--- VAULT INVENTORY REPORT ---")
    print(json.dumps(inventory, indent=2))
    print("\nInventory saved to:", INVENTORY_PATH)

if __name__ == "__main__":
    asyncio.run(main())
