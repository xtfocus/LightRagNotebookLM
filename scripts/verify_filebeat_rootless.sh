#!/bin/bash

set -e

# Verify Filebeat can harvest Docker logs in rootless Docker setups and that events flow to Logstash

# Load DOCKER_ROOT_DIR and FILEBEAT_HTTP_PORT from .env if present
if [ -f ./.env ]; then
  # shellcheck disable=SC2046
  export $(grep -E '^(DOCKER_ROOT_DIR|FILEBEAT_HTTP_PORT)=' ./.env | xargs -d '\n') || true
fi

DOCKER_ROOT_DIR_HOST=${DOCKER_ROOT_DIR:-/var/lib/docker}
FILEBEAT_HTTP_PORT=${FILEBEAT_HTTP_PORT:-5066}

echo "========================================"
echo "Filebeat Rootless Docker Verification"
echo "========================================"

echo "Host DockerRootDir (from env or default): $DOCKER_ROOT_DIR_HOST"
echo "Expecting container logs at: $DOCKER_ROOT_DIR_HOST/containers"

if [ ! -d "$DOCKER_ROOT_DIR_HOST/containers" ]; then
  if command -v sudo >/dev/null 2>&1 && sudo test -d "$DOCKER_ROOT_DIR_HOST/containers"; then
    echo "⚠ Host path exists but requires elevated permissions: $DOCKER_ROOT_DIR_HOST/containers"
    echo "  - Try running this script with sudo OR adjust directory permissions so it's traversable"
    echo "  - Current permissions:"
    ls -ld "$DOCKER_ROOT_DIR_HOST" 2>/dev/null || true
    ls -ld "$DOCKER_ROOT_DIR_HOST/containers" 2>/dev/null || true
  else
    echo "✗ Host path not found: $DOCKER_ROOT_DIR_HOST/containers"
    echo "  - Set DOCKER_ROOT_DIR in .env to your DockerRootDir (docker info | grep DockerRootDir)"
    exit 1
  fi
fi

LOG_COUNT=$(find "$DOCKER_ROOT_DIR_HOST/containers" -name "*-json.log" 2>/dev/null | wc -l | tr -d ' ')
if [ "$LOG_COUNT" = "0" ] && command -v sudo >/dev/null 2>&1; then
  LOG_COUNT=$(sudo find "$DOCKER_ROOT_DIR_HOST/containers" -name "*-json.log" 2>/dev/null | wc -l | tr -d ' ')
fi
echo "Found $LOG_COUNT container log files on host"
if [ "$LOG_COUNT" = "0" ]; then
  echo "⚠ No *-json.log files found on host. Start some containers that emit logs, then retry."
fi

echo "Checking Filebeat container status..."
if ! docker compose ps filebeat | grep -q "Up"; then
  echo "✗ Filebeat is not running. Start with: docker compose --profile elk up -d filebeat"
  exit 1
fi

echo "Checking that Filebeat sees the mounted path..."
MOUNT_COUNT=$(docker compose exec -T filebeat sh -lc 'ls -1 /var/lib/docker/containers 2>/dev/null | wc -l' | tr -d ' ' || echo 0)
echo "Filebeat sees $MOUNT_COUNT entries under /var/lib/docker/containers"
if [ "$MOUNT_COUNT" = "0" ]; then
  echo "✗ Filebeat does not see any logs under /var/lib/docker/containers"
  echo "  - Ensure compose mounts ${DOCKER_ROOT_DIR_HOST}/containers:/var/lib/docker/containers:ro"
  echo "  - Current DOCKER_ROOT_DIR: ${DOCKER_ROOT_DIR_HOST}"
  exit 1
fi

STATS_URL="http://localhost:${FILEBEAT_HTTP_PORT}/stats"
echo "Querying Filebeat stats at ${STATS_URL}"

STATS1=$(curl -sS --max-time 5 "$STATS_URL" || true)
if [ -z "$STATS1" ]; then
  echo "✗ Could not reach Filebeat HTTP endpoint on port ${FILEBEAT_HTTP_PORT}"
  echo "  - Ensure docker-compose publishes ${FILEBEAT_HTTP_PORT}:5066 for filebeat"
  exit 1
fi

# Extract simple metrics without jq
ACK1=$(echo "$STATS1" | grep -o '"acked":[0-9]*' | head -1 | cut -d: -f2)
OPEN1=$(echo "$STATS1" | grep -o '"open_files":[0-9]*' | head -1 | cut -d: -f2)
ACK1=${ACK1:-0}
OPEN1=${OPEN1:-0}
echo "Initial stats: harvesters(open_files)=$OPEN1, events_acked=$ACK1"

echo "Waiting 5s and sampling again..."
sleep 5
STATS2=$(curl -sS --max-time 5 "$STATS_URL" || true)
ACK2=$(echo "$STATS2" | grep -o '"acked":[0-9]*' | head -1 | cut -d: -f2)
OPEN2=$(echo "$STATS2" | grep -o '"open_files":[0-9]*' | head -1 | cut -d: -f2)
ACK2=${ACK2:-0}
OPEN2=${OPEN2:-0}
echo "Second stats: harvesters(open_files)=$OPEN2, events_acked=$ACK2"

if [ "$OPEN2" -eq 0 ]; then
  echo "✗ Filebeat has 0 open harvesters. Likely log path mount is wrong."
  echo "  - Check DOCKER_ROOT_DIR in .env and restart: docker compose --profile elk restart filebeat"
  exit 1
fi

if [ "$ACK2" -gt "$ACK1" ]; then
  echo "✓ Filebeat is harvesting and sending events (acked increased)"
else
  echo "⚠ Acked did not increase. If new logs are not being written, this can be normal."
  echo "  - Generate activity (e.g., docker compose logs agent | head) and rerun"
fi

echo "OK"


