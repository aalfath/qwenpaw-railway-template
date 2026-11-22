#!/bin/sh
# QwenPaw on Railway: prepare the volume, create the login, then exec the app
# and watch it, so the container lives and dies with it. Any failure
# exits non-zero, so Railway's ON_FAILURE restart policy applies.
set -eu

PORT="${PORT:-8088}"
case "$PORT" in ''|*[!0-9]*) echo "[railway] FATAL: PORT '$PORT' is not a number" >&2; exit 1 ;; esac

# This template always requires the console login (agent with shell, file
# and browser tools on a public URL).
export QWENPAW_AUTH_ENABLED=true

if ! awk '$5 == "/data" { f = 1 } END { exit !f }' /proc/self/mountinfo; then
  echo "[railway] WARNING: /data is not a volume; chats, memory, login and API keys are lost on redeploy" >&2
fi

mkdir -p "$QWENPAW_WORKING_DIR" "$QWENPAW_SECRET_DIR" "$QWENPAW_BACKUP_DIR"
chmod 700 "$QWENPAW_SECRET_DIR"
cd /app

# One setup at a time on the volume (overlapping deploys).
flock -w 300 /data/.railway-setup.lock /app/venv/bin/python /railway/setup.py

# The login now lives hashed on the volume; keep it out of the agent's tools.
unset QWENPAW_AUTH_USERNAME QWENPAW_AUTH_PASSWORD QWENPAW_TRUSTED_PROXIES

echo "[railway] starting QwenPaw on 0.0.0.0:${PORT} (login required)" >&2
qwenpaw app --host 0.0.0.0 --port "$PORT" --log-level "${QWENPAW_LOG_LEVEL:-info}" &
app=$!
stopping=0
trap 'stopping=1; kill -TERM "$app" 2>/dev/null' TERM INT
rc=0
wait "$app" || rc=$?
# wait returns early when a trapped signal arrives; wait again for the exit.
if [ "$stopping" = 1 ]; then wait "$app" 2>/dev/null || true; exit 0; fi
# Any stop Railway didn't ask for (crash, OOM, or a clean exit after an
# in-app restart request) exits non-zero, so ON_FAILURE restarts the service.
echo "[railway] QwenPaw stopped (exit $rc); exiting non-zero so Railway restarts it" >&2
[ "$rc" -ne 0 ] || rc=1
exit "$rc"
