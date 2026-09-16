# syntax=docker/dockerfile:1.7

# Instead of rebuilding LiteLLM from source (slow, needs build deps),
# extend the pre-built runtime image and strip the extras we don't need.
# The published image already has all extras; we uninstall the four groups
# the playbook used to exclude at build time: proxy-runtime, semantic-router,
# saml, and bedrock-realtime.

# Pin uv to the same version the official Dockerfile uses
FROM ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a AS uvbin

FROM ghcr.io/berriai/litellm:main-latest

USER root

# Copy uv so we can manage Python packages in the venv
COPY --from=uvbin /uv /usr/local/bin/uv
COPY --from=uvbin /uvx /usr/local/bin/uvx

# The base image has PATH="/app/.venv/bin:..." set, so uv automatically
# targets the right virtual environment.  Uninstall packages from the
# extras we want to drop.
RUN uv pip uninstall \
    # --- proxy-runtime extras ---
    google-cloud-aiplatform \
    google-genai \
    anthropic \
    grpcio \
    prometheus-client \
    langfuse \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-fastapi \
    ddtrace \
    sentry-sdk \
    mangum \
    azure-ai-contentsafety \
    azure-storage-file-datalake \
    pypdf \
    llm-sandbox \
    detect-secrets \
    # --- semantic-router extras ---
    semantic-router \
    aurelio-sdk \
    # --- saml extras ---
    python3-saml \
    # --- bedrock-realtime extras ---
    aws-sdk-bedrock-runtime

# Purge uv's download / build cache — no need at runtime
RUN rm -rf /root/.cache/uv
