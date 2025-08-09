# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv (fast pip replacement) and cache wheels/downloads across builds
RUN --mount=type=cache,target=/root/.cache,id=uv \
    python -m pip install --no-cache-dir uv

COPY requirements.txt /app/requirements.txt

# Use uv for faster dependency install with cache mount
RUN --mount=type=cache,target=/root/.cache,id=uv \
    uv pip install --system -r /app/requirements.txt

COPY holiday_calendar.py /app/holiday_calendar.py

CMD ["python", "/app/holiday_calendar.py"]
