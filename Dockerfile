FROM python:3.12-slim

WORKDIR /app

# install system packages
RUN apt update \
 && apt install -y --no-install-recommends \
      build-essential \
      libglib2.0-0 \
      libsm6 libxext6 libxrender1 libgl1 \
      curl

# copy prebuilt wheel
COPY dist/*.whl /dist/

# install without going to PyPI
RUN pip install \
    --find-links=/dist \
    workspace_monitor

ENTRYPOINT ["python","-m","workspace_monitor.main"]
