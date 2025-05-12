FROM python:3.12-slim

WORKDIR /app

# install system packages
RUN apt update \
 && apt install -y --no-install-recommends \
      build-essential \
      libsm6 libxext6 libxrender1 libgl1 \
      curl

# install uv (https://docs.astral.sh/uv/guides/integration/docker/#installing-uv)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# setup the project
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY workspace_monitor/ workspace_monitor/

ENTRYPOINT ["uv", "run", "workspace-monitor"]
