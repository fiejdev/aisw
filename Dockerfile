FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /opt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy pandas requests bs4

COPY harness.py /opt/harness.py

USER 65534:65534

ENTRYPOINT ["python", "-u", "/opt/harness.py"]