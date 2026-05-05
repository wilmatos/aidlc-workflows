# AIDLC MCP Server

AI Development Life Cycle workflow guidance server, built on [FastMCP](https://github.com/jlowin/fastmcp).

Dynamically loads workflow instructions from the bundled `aidlc-rules/` directory and guides LLM agents through a structured software development process. All project state lives in the user's workspace — the server is stateless.

## Quick Start

### Option 1: uvx (recommended for end users)

No installation needed — `uvx` downloads and runs the server in an isolated environment:

```bash
uvx aidlc-mcp-server
```

### Option 2: pip install

```bash
pip install aidlc-mcp-server
aidlc-mcp-server
```

### From source (development)

```bash
git clone <this-monorepo>
cd aidlc-mcp-server
pip install -e ".[dev]"
./scripts/sync-aidlc-rules.sh   # Copy rules from monorepo root
aidlc-mcp-server
```

Workflow rules are bundled inside the package, so both `uvx` and `pip install` work out of the box. You can override the rules directory at runtime with `--workflow-dir /path/to/aidlc-rules` or the `AIDLC_WORKFLOW_DIR` environment variable.

## MCP Client Configuration

### Using uvx (no install required)

```json
{
  "mcpServers": {
    "aidlc": {
      "command": "uvx",
      "args": ["aidlc-mcp-server"]
    }
  }
}
```

### Using pip install

```json
{
  "mcpServers": {
    "aidlc": {
      "command": "aidlc-mcp-server",
      "args": []
    }
  }
}
```

Rules are bundled inside the package — no `cwd` or environment variables needed.

## Tools

| Tool | Purpose |
|------|---------|
| `aidlc_start_project` | Create a new project with operational mode |
| `aidlc_get_guidance` | Load workflow/stage guidance dynamically |
| `aidlc_complete_stage` | Save deliverable, advance to next stage |
| `aidlc_list_projects` | List all projects in workspace |
| `aidlc_log` | Append to project audit log |
| `aidlc_manage_extensions` | List/read workflow extensions |

## How It Works

1. The server reads all workflow logic from markdown files in `aidlc-rules/` (bundled inside the package, or from the monorepo root during development)
2. `aws-aidlc-rules/core-workflow.md` is the main orchestration file
3. Stage-specific guidance lives in `aws-aidlc-rule-details/{phase}/{stage}.md`
4. Editing any workflow file takes effect immediately (mtime-based cache)
5. Extensions in `aws-aidlc-rule-details/extensions/` add domain-specific guidance (scanned recursively)

## Workflow Phases

The AIDLC workflow has 3 phases with 13+ stages:

**Inception** — Planning and requirements
- Workspace Detection → Reverse Engineering → Requirements Analysis → User Stories → Workflow Planning → Application Design → Units Generation

**Construction** — Design and implementation (per-unit loop)
- Functional Design → NFR Requirements → NFR Design → Infrastructure Design → Code Generation → Build and Test

**Operations** — Deployment and monitoring (placeholder)

## Extensions

Extensions live under `aidlc-rules/aws-aidlc-rule-details/extensions/` and can be nested in subdirectories. The server scans recursively, matching the upstream `core-workflow.md` expectation.

```text
extensions/
  security/
    baseline/
      security-baseline.md
  react-frontend.md
```

Extension names include their relative path (e.g. `security/baseline/security-baseline`). Use `aidlc_manage_extensions` with `action='list'` to discover available extensions, and `action='read'` with the full relative name to load one.

## Project Structure

```text
aidlc_mcp_server/              # Server code
├── server.py                  # FastMCP tools and resources
├── workflow_loader.py         # Dynamic file loading with cache
├── project.py                 # Project state management
├── validation.py              # Input validation and path safety
├── main.py                    # CLI entry point
├── __init__.py
├── __version__.py
└── aidlc-rules/               # Bundled workflow rules (included in wheel)
    ├── .sync-metadata
    ├── aws-aidlc-rules/
    └── aws-aidlc-rule-details/

aidlc-rules/                   # Workflow content (copied from monorepo root)
├── .sync-metadata             # Provenance: monorepo commit, sync timestamp
├── aws-aidlc-rules/           # Core workflow orchestration
│   └── core-workflow.md
└── aws-aidlc-rule-details/    # Stage-specific guidance
    ├── common/                # Shared rules (validation, question format, etc.)
    ├── inception/             # Inception phase stages
    ├── construction/          # Construction phase stages
    ├── operations/            # Operations phase stages
    └── extensions/            # Domain-specific extensions (nested subdirs supported)

scripts/
├── sync-aidlc-rules.sh       # Copy rules from monorepo root
├── sync-and-test-rules.sh    # Sync + run tests
└── generate-build-info.sh    # Write build metadata into _build_info.py
```

The `aidlc-rules/` directory exists in two places:
- **Repo root** (`aidlc-rules/`) — used during development, editable for hot-reload
- **Inside the package** (`aidlc_mcp_server/aidlc-rules/`) — bundled into wheels for distribution

## Syncing Workflow Rules

The workflow rules live in the monorepo root at `../aidlc-rules/`. The sync script copies them into the MCP server's local directories.

```bash
# Copy rules from monorepo root
./scripts/sync-aidlc-rules.sh
```

The script copies the `aidlc-rules/` folder to both the local repo root and inside the Python package (`aidlc_mcp_server/aidlc-rules/`), and writes `.sync-metadata` files with the monorepo commit hash and timestamp for provenance tracking.

You can override the rules directory at runtime via the `AIDLC_WORKFLOW_DIR` environment variable or the `--workflow-dir` CLI flag. When neither is set, the server looks for bundled rules inside the package first, then falls back to the repo root.

## Development

```bash
cd aidlc-mcp-server
pip install -e ".[dev]"
./scripts/sync-aidlc-rules.sh    # Copy rules from monorepo root
pytest                            # Run tests
ruff check .                      # Lint
```

## Packaging and Distribution

The GitLab CI pipeline (`.gitlab-ci.yml`) handles building and releasing. Workflow rules are bundled inside the Python package as package data, so both `pip install` and `uvx` users get the rules automatically — no `AIDLC_WORKFLOW_DIR`, `cwd`, or manual setup needed.

```bash
# End users can run directly with uvx
uvx aidlc-mcp-server

# Or install with pip
pip install aidlc-mcp-server
aidlc-mcp-server
```

### How versioning works

Two versions are tracked independently:

- Server version: set in `aidlc_mcp_server/__version__.py` (e.g. `1.0.0`)
- Rules version: captured from `aidlc-rules/.sync-metadata` (monorepo commit hash)

Both are baked into `_build_info.py` at build time by `scripts/generate-build-info.sh` and shown via `aidlc-mcp-server --version`.

### Pipeline stages

| Stage | Trigger | What it does |
|-------|---------|--------------|
| `test` | MR or push to main | Runs pytest + ruff with bundled rules |
| `build` | Push to main or tag | Syncs rules from monorepo root, builds wheel + Docker image |
| `release` | Git tag (e.g. `v1.2.0`) | Creates a GitLab release with artifacts |

### Creating a release

```bash
# 1. Bump version
# Edit aidlc_mcp_server/__version__.py

# 2. Tag and push
git tag v1.2.0
git push origin v1.2.0
```

The pipeline will build the wheel, push a Docker image, and create a GitLab release.

### Distribution tarball

The build produces a tarball containing:

```text
aidlc-mcp-server-1.2.0/
├── aidlc_mcp_server-1.2.0-py3-none-any.whl   # Rules bundled inside
├── install.sh            # pip install + usage instructions
├── README.md
└── LICENSE
```

The wheel includes the workflow rules as package data. Recipients can either:
- Run `pip install *.whl` and then `aidlc-mcp-server`
- Or use `uvx aidlc-mcp-server` if the package is published to PyPI

## License

MIT
