# Configure

First run `pictureme auth login` in a trusted terminal. Configure your MCP host with the absolute executable path appropriate to your own installation:

```json
{
  "mcpServers": {
    "pictureme": {
      "command": "/path/to/venv/bin/pictureme-mcp",
      "env": {"PICTUREME_HOST": "https://go.pictureme.now"}
    }
  }
}
```

Alternatively inject `PICTUREME_API_KEY` via a secret manager into the process environment. Do not store a real key in committed MCP JSON. The server uses the CLI's platformdirs config and credential protections; POSIX persisted keys are mode-0600 plaintext, not encrypted. Non-POSIX persistence is refused. Authenticated operations require an account, appropriate scopes, service access and credits. Client MIT licensing does not grant any of those.


[Documentation index](README.md) · [Project overview](../README.md)
