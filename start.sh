#!/bin/sh
set -e

# Start the backend process in the background
eval "$BACKEND_CMD" &

# Start Caddy in the foreground (keeps the container alive)
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
