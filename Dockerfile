# Dockerfile for AppDaemon Z-Wave Entity Mapper Utility
# Based on official minimal Python image (3.11-slim)
# Builds AppDaemon in a venv, copies required scripts, exposes default ports.
# Usage: See README.md for build and run instructions.

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory and venv
WORKDIR /app

# Install system dependencies if needed (minimal for appdaemon)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install appdaemon \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:$PATH"

# Copy AppDaemon apps and config
# Expects /conf to be mounted as config directory; /app contains defaults as fallback/sample
COPY apps/zwave_entity_mapper.py /app/apps/zwave_entity_mapper.py
COPY apps/zwave_entity_mapping.yaml /app/apps/zwave_entity_mapping.yaml
# Copy entire apps/ dir to support further appdaemon scripts if desired
COPY apps/ /app/apps/
# Copy any default config (user must mount writable or persistent config at runtime)
COPY . /app/

# Create mount point for config (external volume to persist configuration)
VOLUME ["/conf"]

# Expose AppDaemon default web and dashboard ports
EXPOSE 5050 5051

# By default, run AppDaemon using /conf as the config directory.
# Pass environment vars or override CMD to customize.
ENTRYPOINT ["/opt/venv/bin/appdaemon"]
CMD ["-c", "/conf"]

# Essential usage:
# docker build -t appdaemon-zwave-mapper .
# docker run -p 5050:5050 -p 5051:5051 -v /local/path/to/config:/conf appdaemon-zwave-mapper
