# pictureme-mcp

Stdio Model Context Protocol client for the hosted PictureME API, maintained by **Jesus Pacheco / Akitá Labs**. Reuses the separately packaged `pictureme-cli` HTTP client. This is not a self-hosted backend.

## Install

Python 3.10+. Public target: https://github.com/Pachecodes/pictureme-mcp-public.
The shared CLI must be installed from an **approved artifact first**. These
repository names are publication targets, not a claim that they already exist.
No package-index publication or ownership is asserted; do not install a package
by name from an index and assume it is ours.

From an approved standalone MCP checkout, install a maintainer-reviewed CLI wheel
whose SHA-256 you have verified against the release record:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install /path/to/approved/pictureme_cli-0.1.0-py3-none-any.whl
python -m pip install .
python -m pip check
```

Alternatively, after the public CLI repository is available, use its reviewed
immutable commit (replace `APPROVED_CLI_COMMIT` with the actual approved SHA):

```bash
python -m pip install "pictureme-cli @ git+https://github.com/Pachecodes/pictureme-cli-public.git@APPROVED_CLI_COMMIT"
python -m pip install .
```

Use a fresh venv, keep the approved CLI installed, and do not use `--upgrade` or
`--force-reinstall` on MCP with dependency resolution: that can replace the CLI
with an unrelated index package. Dependencies other than the shared CLI are
ordinary separately licensed packages. For wheel-only installation, install the
approved CLI wheel first and then the approved MCP wheel. CI explicitly checks
out the corresponding public CLI repository, builds it and installs that wheel
before MCP; it does not assume `pictureme-cli` exists on PyPI. Maintainers must
review both exact Git SHAs and wheel digests before accepting a release.

## Configure

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

## Tools and authorization

- `pictureme_model_list`, `pictureme_model_get`: catalog/schema reads.
- `pictureme_upload_file`: uploads a **local file**, not a remote URL. This discloses its contents to the service. Restrict the agent's filesystem permissions.
- `pictureme_generate_create`: submits a paid generation; require explicit user authorization.
- `pictureme_generate_get`, `pictureme_generate_list`, `pictureme_generate_wait`: job reads/polling.
- `pictureme_generate_cancel`: cancellation request, not a guaranteed provider stop or refund.
- `pictureme_generate_cost`: local catalog-based estimate, NOT an authoritative quote; pricing rules may be more complex and billing is server-owned.
- `pictureme_token_balance`, `pictureme_token_transactions`: account reads requiring service permission.

Read tools can expose private account/job data to the MCP host. Use only trusted hosts and agents. There is no admin tool. Server authorization still applies. Never assume balance proves a job is affordable or cancellation means a refund. Read catalog/schema, present a nonbinding estimate, obtain approval before upload or paid submission, and inspect final status. API errors are returned without raw error bodies. All shared-client redirects
are disabled; 3xx responses fail without forwarding passwords, device exchange
codes or media to the redirect target.

## Development and license

Install the approved CLI package, then `python -m pip install -e '.[dev]'`.
Run `python -m pytest -q` and `python -m build`. Tests are offline and use no paid generation. See SECURITY.md, CONTRIBUTING.md and PROVENANCE.md. MIT applies to original clients only, not the hosted service, dependencies, models, trademarks or media.
