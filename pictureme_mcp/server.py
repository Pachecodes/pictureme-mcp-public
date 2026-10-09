"""MCP stdio server exposing PictureME v3 tools.

Uses the `mcp` Python SDK's FastMCP helper so each tool is a plain
typed Python function decorated with @mcp.tool(). The actual HTTP work
is delegated to pictureme.client (shipped by the pictureme-cli sibling
package) so the CLI and the MCP server stay byte-identical against the
backend.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from pictureme.client import APIError, PictureMEClient
from pictureme.config import resolve_runtime

mcp = FastMCP("pictureme")


def _client() -> PictureMEClient:
    """Build a fresh client per call so token rotations land immediately."""
    cfg = resolve_runtime()
    return PictureMEClient(cfg)


def _safe(call):
    """Wrap an HTTP-backed call so APIError becomes a structured tool result."""
    try:
        return call()
    except APIError as exc:
        return {
            "error": "PictureME request failed",
            "status_code": exc.status_code,
        }


@mcp.tool()
def pictureme_model_list(
    image_only: bool = False,
    video_only: bool = False,
    provider: Optional[str] = None,
) -> dict[str, Any]:
    """List the active PictureME models from the public registry.

    Useful before picking a model_id for pictureme_generate_create.
    """
    def _go() -> dict[str, Any]:
        with _client() as c:
            payload = c.get("/api/v3/public/models")
        models = payload.get("models", [])
        if image_only:
            models = [m for m in models if m.get("model_type") == "image"]
        if video_only:
            models = [m for m in models if m.get("model_type") == "video"]
        if provider:
            models = [m for m in models if m.get("provider") == provider]
        return {"models": models}

    return _safe(_go)


@mcp.tool()
def pictureme_model_get(model_id: str) -> dict[str, Any]:
    """Fetch one model's full registry entry (input_schema, media_inputs, cost rules)."""
    def _go() -> dict[str, Any]:
        with _client() as c:
            return c.get(f"/api/v3/public/models/{model_id}")
    return _safe(_go)


@mcp.tool()
def pictureme_upload_file(path: str) -> dict[str, Any]:
    """Upload a local file (absolute or relative path) to the backend's R2 staging.

    Returns the URL that pictureme_generate_create can reference as media.
    """
    p = Path(path).expanduser()
    if not p.exists() or not p.is_file():
        return {"error": f"file not found: {path}"}

    def _go() -> dict[str, Any]:
        with _client() as c:
            with p.open("rb") as fh:
                files = {"file": (p.name, fh, "application/octet-stream")}
                return c.post("/api/v3/creator/generate/upload", files=files)

    return _safe(_go)


@mcp.tool()
def pictureme_generate_create(
    model_id: str,
    prompt: str,
    images: Optional[list[str]] = None,
    first_frame: Optional[str] = None,
    last_frame: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    duration: Optional[str] = None,
    output_format: Optional[str] = None,
    seed: Optional[int] = None,
    num_images: Optional[int] = None,
    generate_audio: Optional[bool] = None,
    visibility: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> dict[str, Any]:
    """Create a generation job (image or video).

    `images`, `first_frame`, `last_frame` must already be URLs — call
    pictureme_upload_file first if you only have local paths. Returns the
    initial job snapshot; poll with pictureme_generate_get or block with
    pictureme_generate_wait.
    """
    media: dict[str, Any] = {}
    if images:
        media["images"] = list(images)
    if first_frame:
        media["first_frame"] = first_frame
    if last_frame:
        media["last_frame"] = last_frame

    params: dict[str, Any] = {}
    if aspect_ratio is not None:
        params["aspect_ratio"] = aspect_ratio
    if resolution is not None:
        params["resolution"] = resolution
    if duration is not None:
        params["duration"] = duration
    if output_format is not None:
        params["output_format"] = output_format
    if seed is not None:
        params["seed"] = seed
    if num_images is not None:
        params["num_images"] = num_images
    if generate_audio is not None:
        params["generate_audio"] = generate_audio

    body: dict[str, Any] = {
        "model_id": model_id,
        "prompt": prompt,
        "media": media,
        "params": params,
    }
    if visibility is not None:
        body["visibility"] = visibility
    if parent_id is not None:
        body["parent_id"] = parent_id

    def _go() -> dict[str, Any]:
        with _client() as c:
            return c.post("/api/v3/shared/generate/jobs", json=body)

    return _safe(_go)


@mcp.tool()
def pictureme_generate_get(job_id: int) -> dict[str, Any]:
    """Fetch one job's current state."""
    def _go() -> dict[str, Any]:
        with _client() as c:
            return c.get(f"/api/v3/shared/generate/jobs/{job_id}")
    return _safe(_go)


@mcp.tool()
def pictureme_generate_list(
    kind: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """List recent jobs for the authenticated user."""
    params: dict[str, Any] = {}
    if kind:
        params["kind"] = kind
    if status:
        params["status"] = status

    def _go() -> dict[str, Any]:
        with _client() as c:
            return c.get("/api/v3/shared/generate/jobs", params=params)
    return _safe(_go)


_TERMINAL = {"completed", "failed", "cancelled"}


@mcp.tool()
def pictureme_generate_wait(
    job_id: int,
    timeout_seconds: int = 300,
    interval_seconds: int = 3,
) -> dict[str, Any]:
    """Poll a job until it reaches a terminal state, or timeout.

    Returns the final job snapshot. Use this when the agent needs the
    generated URL before continuing instead of returning to the user
    for a manual check.
    """
    deadline = time.monotonic() + max(1, timeout_seconds)
    interval = max(1, interval_seconds)
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        try:
            with _client() as c:
                last = c.get(f"/api/v3/shared/generate/jobs/{job_id}")
        except APIError as exc:
            return {"error": str(exc), "status_code": exc.status_code}
        if last.get("status") in _TERMINAL:
            return last
        time.sleep(interval)
    return {**last, "timed_out": True}


@mcp.tool()
def pictureme_generate_cancel(job_id: int) -> dict[str, Any]:
    """Mark a job cancelled. Upstream provider may still complete it server-side."""
    def _go() -> dict[str, Any]:
        with _client() as c:
            return c.post(f"/api/v3/shared/generate/jobs/{job_id}/cancel")
    return _safe(_go)


@mcp.tool()
def pictureme_generate_cost(
    model_id: str,
    resolution: Optional[str] = None,
    audio: Optional[bool] = None,
    duration: Optional[str] = None,
    num_images: int = 1,
) -> dict[str, Any]:
    """Estimate token cost locally without submitting a generation.

    This nonbinding estimate uses public catalog fields, not an authoritative
    quote. Server-owned billing rules and final charges may differ. Obtain
    explicit user approval before paid submission.
    """
    def _go() -> dict[str, Any]:
        with _client() as c:
            m = c.get(f"/api/v3/public/models/{model_id}")
        base = int(m.get("default_cost", 0))
        rules = m.get("cost_rules") or {}
        extra = 0

        def _rule_for(param: str, value: Any) -> int:
            if value is None:
                return 0
            bucket = rules.get(param)
            if not isinstance(bucket, dict):
                return 0
            cell = bucket.get(str(value))
            if isinstance(cell, (int, float)):
                return int(cell)
            return 0

        extra += _rule_for("resolution", resolution)
        if audio is not None:
            extra += _rule_for("audio", audio)
        extra += _rule_for("duration", duration)
        per_call = base + extra
        total = per_call * max(1, num_images)
        return {
            "model_id": m.get("model_id"),
            "base_cost": base,
            "extra_cost": extra,
            "per_call_cost": per_call,
            "num_images": num_images,
            "total_cost": total,
        }

    return _safe(_go)


@mcp.tool()
def pictureme_token_balance() -> dict[str, Any]:
    """Get the authenticated user's current token balance.

    Check this before creating jobs so the agent can warn about (or avoid)
    generations the user can't afford. Requires tokens:read scope on API keys.
    """
    def _go() -> dict[str, Any]:
        with _client() as c:
            return c.get("/api/v3/shared/tokens/balance")
    return _safe(_go)


@mcp.tool()
def pictureme_token_transactions(limit: int = 20) -> dict[str, Any]:
    """List recent token transactions (charges, refunds, purchases).

    Useful for auditing what generations cost, confirming refunds after
    failed/cancelled jobs, and explaining balance changes to the user.
    """
    def _go() -> dict[str, Any]:
        with _client() as c:
            payload = c.get("/api/v3/shared/tokens/transactions", params={"limit": limit})
        if isinstance(payload, list):
            return {"transactions": payload}
        return payload

    return _safe(_go)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
