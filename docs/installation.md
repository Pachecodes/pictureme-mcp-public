# Install

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


[Documentation index](README.md) · [Project overview](../README.md)
