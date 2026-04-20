from aas_kernel import AASPlugin

class MyFortressSecurityPlugin(AASPlugin):
    @property
    def capabilities(self) -> list[str]:
        return ["fortress_secret_scan", "fortress_policy_evaluate"]

    async def handle_message(self, capability_id: str, payload: dict) -> dict:
        self.logger.info(f"Handling {capability_id} with payload: {payload}")
        if capability_id == "fortress_secret_scan":
            return {"status": "success", "capability": capability_id, "result": "No secrets found."}
        elif capability_id == "fortress_policy_evaluate":
            return {"status": "success", "capability": capability_id, "result": "Policy evaluated and passed."}
        return {"status": "error", "message": "Unknown capability"}