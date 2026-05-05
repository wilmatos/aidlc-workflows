# AIDLC MCP Server
FROM python:3.13-slim AS builder

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY aidlc_mcp_server/ ./aidlc_mcp_server/
COPY scripts/ ./scripts/

# Copy rules from monorepo (must be synced before docker build, or use
# build context from monorepo root with: docker build -f aidlc-mcp-server/Dockerfile .)
COPY aidlc-rules/ ./aidlc-rules/

# Ensure rules are also bundled inside the package
RUN cp -R aidlc-rules/ aidlc_mcp_server/aidlc-rules/

# Generate build info
RUN pip install --no-cache-dir -e . && ./scripts/generate-build-info.sh

# --- Runtime stage ---
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/aidlc-mcp-server /usr/local/bin/aidlc-mcp-server

RUN useradd --create-home --shell /bin/bash aidlc
USER aidlc

ENV AIDLC_LOG_LEVEL=INFO

CMD ["aidlc-mcp-server"]
