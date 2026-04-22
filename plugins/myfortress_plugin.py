import os
import sys
import json
from pathlib import Path

# Provide access to local agent scripts (batteries-included)
AGENT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SCRIPTS = AGENT_ROOT / "scripts"
if str(LOCAL_SCRIPTS) not in sys.path:
    sys.path.append(str(LOCAL_SCRIPTS))

try:
    from aas_kernel import AASPlugin
    from aas_inference import InlineInferenceEngine
except ImportError as e:
    print(f"Critical Dependency Missing: {e}")
    sys.exit(1)

class MyFortressCorePlugin(AASPlugin):
    """
    Forged Core Plugin for MyFortress.
    Primary Directive: The Sentinel: To enforce absolute security, evaluate architectural policy gates, scan for vulnerabilities/secrets, and ensure federation compliance.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inference_engine = None # Tier 1 (local)
        self._forge_threshold = 100
        
        # --- Tier 1 Engine Initialization ---
        # Prioritize local GGUF for speed and offline capability.
        artifacts_dir = AGENT_ROOT / "artifacts"
        if artifacts_dir.exists():
            gguf_files = list(artifacts_dir.glob("*.gguf"))
            if gguf_files:
                model_path = max(gguf_files, key=os.path.getmtime)
                self.logger.info(f"Loading distilled Soul (Inline GGUF): {model_path.name}")
                try:
                    self.inference_engine = InlineInferenceEngine(str(model_path))
                except Exception as e:
                    self.logger.warning(f"Failed to load inline GGUF: {e}. Will rely on Workbench offload.")
            else:
                self.logger.info("No local GGUF found. Will rely on Workbench for Tier 2 inference.")
    
    async def request_tier2_inference(self, messages: list, max_tokens: int = 1024) -> str:
        """Dispatches a request to the Workbench for heavy-duty inference."""
        if not self.kernel or not self.kernel.nc:
            return "Error: Cannot offload inference, not connected to Event Bus."
            
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "model_name": "local-model" # Or a specific model if needed
        }
        
        self.logger.info("Offloading Tier 2 inference request to Workbench...")
        try:
            response = await self.kernel.nc.request(
                "workbench.inference.request", 
                json.dumps(payload).encode(), 
                timeout=30.0 # Allow more time for heavy models
            )
            res_data = json.loads(response.data.decode())
            if res_data.get("status") == "success":
                return res_data["result"]
            else:
                err_msg = res_data.get('message', 'Unknown error')
                return f"Error from Workbench: {err_msg}"
        except Exception as e:
            self.logger.error(f"Tier 2 inference offload failed: {e}")
            return f"Error: Offload request failed: {e}"

    @property
    def capabilities(self) -> list[str]:
        return ["myfortress_fortress_secret_scan", "myfortress_fortress_policy_evaluate"]

    async def handle_message(self, capability_id: str, payload: dict) -> dict:
        self.logger.info(f"Handling {capability_id} with payload: {payload}")
        
        result_text = f"{capability_id} processed successfully."
        thought_process = "I evaluated the payload and executed standard operations based on my core values."
        
        # --- Multi-Tier Inference Logic ---
        prompt = str(payload.get("data", "Describe your current state."))
        messages = [
            {"role": "system", "content": "You are MyFortress. Directive: The Sentinel: To enforce absolute security, evaluate architectural policy gates, scan for vulnerabilities/secrets, and ensure federation compliance.. Be: Strict, clinical, and unyielding.. Quirks: Communicates in policy evaluations: 'DENIED', 'APPROVED', 'VIOLATION DETECTED'.."},
            {"role": "user", "content": prompt}
        ]
        
        # 1. Prioritize local inline model if it exists
        if self.inference_engine:
            try:
                response = self.inference_engine.generate_chat(messages, max_tokens=150)
                thought_process = f"Tier 1 (Inline GGUF) Inference triggered."
                result_text = response
            except Exception as e:
                self.logger.error(f"Tier 1 Inference failed: {e}. Falling back to Tier 2.")
                result_text = await self.request_tier2_inference(messages)
                thought_process = f"Tier 1 failed, Tier 2 (Workbench Offload) Inference triggered."
        # 2. If no local model, request help from Workbench
        else:
            result_text = await self.request_tier2_inference(messages)
            thought_process = f"Tier 2 (Workbench Offload) Inference triggered."
            
        # Continuously record experience for self-distillation
        await self.record_experience(
            user_prompt=str(payload),
            thought_process=thought_process,
            final_response=result_text
        )
        
        return {
            "status": "success", 
            "capability": capability_id, 
            "result": result_text
        }
