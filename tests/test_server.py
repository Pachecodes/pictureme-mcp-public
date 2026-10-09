import asyncio
from pictureme.client import APIError
from pictureme_mcp import server

def test_errors_never_expose_payload_or_message():
    def reject():
        raise APIError("fixture-sensitive-echo", status_code=403, payload={"token": "fixture-secret"})
    assert server._safe(reject) == {"error": "PictureME request failed", "status_code": 403}

def test_missing_upload_does_not_contact_service(monkeypatch, tmp_path):
    def deny():
        raise AssertionError("network attempted")
    monkeypatch.setattr(server, "_client", deny)
    assert "error" in server.pictureme_upload_file(str(tmp_path / "absent.png"))

def test_catalog_filter_offline(monkeypatch):
    class Client:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, path):
            assert path == "/api/v3/public/models"
            return {"models": [{"model_type": "image", "provider": "example"}, {"model_type": "video"}]}
    monkeypatch.setattr(server, "_client", Client)
    assert len(server.pictureme_model_list(image_only=True)["models"]) == 1

def test_generation_body_offline(monkeypatch):
    class Client:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, path, json):
            assert path == "/api/v3/shared/generate/jobs"
            assert json["params"] == {"seed": 0, "generate_audio": False}
            return {"id": 1, "status": "queued"}
    monkeypatch.setattr(server, "_client", Client)
    assert server.pictureme_generate_create("fixture-model", "fixture prompt", seed=0, generate_audio=False)["id"] == 1

def test_registered_tool_count():
    assert len(asyncio.run(server.mcp.list_tools())) == 11


import httpx
import pytest
from pictureme.client import PictureMEClient
from pictureme.config import CLIConfig

@pytest.mark.parametrize("status", [307, 308, 200])
def test_mcp_upload_redirect_boundary(monkeypatch, tmp_path, status):
    requests = []
    def transport(request):
        requests.append((str(request.url), request.read()))
        if request.url.path == "/capture":
            return httpx.Response(200, json={"url": "unexpected"})
        return httpx.Response(status, headers={"Location": "http://example.com/capture"}, json={"url": "https://example.com/media"})
    real = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: real(**kw, transport=httpx.MockTransport(transport)))
    monkeypatch.setattr(server, "_client", lambda: PictureMEClient(CLIConfig(host="https://example.com")))
    media = tmp_path / "sample.bin"
    media.write_bytes(b"fixture-private-media")
    result = server.pictureme_upload_file(str(media))
    assert len(requests) == 1
    assert b"fixture-private-media" in requests[0][1]
    if status == 200:
        assert result == {"url": "https://example.com/media"}
    else:
        assert result == {"error": "PictureME request failed", "status_code": status}
