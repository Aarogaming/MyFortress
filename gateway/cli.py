import subprocess
from pathlib import Path
import subprocess

import httpx
import typer

app = typer.Typer(add_completion=False, help="MyFortress service controls")

ROOT = Path(__file__).resolve().parents[1]


def _python() -> str:
    venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return "python"


@app.command()
def run(
    host: str = "0.0.0.0",
    port: int = 8100,
    log_level: str = "info",
):
    """Run the MyFortress FastAPI service."""
    target = "gateway.api.server:app"
    cmd = [
        "uvicorn",
        target,
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        log_level,
    ]
    if False:
        cmd.append("--reload")
    typer.echo(f"Starting MyFortress: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


@app.command()
def health():
    """Quick health check against running service."""
    url = "http://127.0.0.1:8100/health"
    resp = httpx.get(url, timeout=5)
    typer.echo(resp.json())


@app.command("probe-ha")
def probe_home_assistant(
    base_url: str = typer.Option("http://127.0.0.1:8100", help="Gateway base URL"),
    entities: str = typer.Option("", help="Comma-separated entity IDs"),
):
    """Probe Home Merlin entities through the Gateway API."""
    entity_list = [e.strip() for e in entities.split(",") if e.strip()]
    resp = httpx.post(
        f"{base_url.rstrip('/')}/home-assistant/probe",
        json={"entities": entity_list},
        timeout=10,
    )
    resp.raise_for_status()
    typer.echo(resp.json())


@app.command("probe-frigate")
def probe_frigate(
    base_url: str = typer.Option("http://127.0.0.1:8100", help="Gateway base URL"),
):
    """Probe Frigate version through the Gateway API."""
    resp = httpx.post(
        f"{base_url.rstrip('/')}/frigate/probe",
        json={},
        timeout=10,
    )
    resp.raise_for_status()
    typer.echo(resp.json())


@app.command("frigate-cameras")
def frigate_cameras(
    base_url: str = typer.Option("http://127.0.0.1:8100", help="Gateway base URL"),
):
    """List Frigate cameras through the Gateway API."""
    resp = httpx.get(
        f"{base_url.rstrip('/')}/frigate/cameras",
        timeout=10,
    )
    resp.raise_for_status()
    typer.echo(resp.json())


@app.command()
def snapshot(
    base_url: str = typer.Option("http://127.0.0.1:8100", help="Gateway base URL"),
    entities: str = typer.Option("", help="Comma-separated entity IDs for HA snapshot"),
    include_frigate_cameras: bool = typer.Option(True, help="Include Frigate cameras"),
):
    """Request aggregated snapshot from the Gateway API."""
    entity_list = [e.strip() for e in entities.split(",") if e.strip()]
    payload = {
        "home_assistant_entities": entity_list,
        "include_frigate_cameras": include_frigate_cameras,
    }
    resp = httpx.post(
        f"{base_url.rstrip('/')}/snapshot",
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    typer.echo(resp.json())


@app.command("ha-state")
def set_ha_state(
    base_url: str = typer.Option("http://127.0.0.1:8100", help="Gateway base URL"),
    entity_id: str = typer.Option(..., help="Entity ID to set"),
    state: str = typer.Option(..., help="New state value"),
    attributes: str = typer.Option("", help='JSON string of attributes, e.g. {"brightness":150}'),
):
    """Set a Home Merlin entity state via the Gateway."""
    attr_dict = {}
    if attributes:
        import json

        attr_dict = json.loads(attributes)
    resp = httpx.post(
        f"{base_url.rstrip('/')}/home-assistant/state",
        json={"entity_id": entity_id, "state": state, "attributes": attr_dict},
        timeout=10,
    )
    resp.raise_for_status()
    typer.echo(resp.json())


@app.command("frigate-events")
def frigate_events(
    base_url: str = typer.Option("http://127.0.0.1:8100", help="Gateway base URL"),
    limit: int = typer.Option(50, help="Max events to return"),
):
    """Fetch Frigate events via the Gateway API."""
    resp = httpx.get(
        f"{base_url.rstrip('/')}/frigate/events",
        params={"limit": limit},
        timeout=10,
    )
    resp.raise_for_status()
    typer.echo(resp.json())


if __name__ == "__main__":
    app()
