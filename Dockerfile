# The Streamlit app as one image. The generated data (out/, results/, data/cache/) is not baked in:
# deploy/compose.yaml mounts it from volumes and the build-data job fills them. See deploy/README.md.
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
COPY app ./app
COPY scripts ./scripts
COPY experiments ./experiments
COPY web ./web
COPY data ./data
COPY docs ./docs
COPY deploy/build-data.sh ./deploy/build-data.sh
RUN uv sync --locked --no-dev

# provenance.stamp() reads the commit from git; there is no .git in the image, so pass it in.
ARG GIT_COMMIT=unknown
ENV DCOPT_GIT_COMMIT=${GIT_COMMIT}

RUN useradd --create-home --uid 10001 app \
    && mkdir -p out results data/cache \
    && chown -R app:app out results data
USER app

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).status == 200 else 1)"

CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", \
     "--server.fileWatcherType=none", "--server.runOnSave=false", \
     "--browser.gatherUsageStats=false", "--client.toolbarMode=minimal"]
