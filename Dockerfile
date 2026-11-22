# QwenPaw for Railway: the official image plus a small start script.
#
# Pinned by version and by the multi-arch index digest of
# agentscope/qwenpaw:v2.3.0.post1 (published 2026-11-18). To update, change
# both, read upstream's release notes and add a CHANGELOG.md entry.
FROM agentscope/qwenpaw:v2.3.0.post1@sha256:033d30887bbb5563ee8ed20a43073ddd7ee93290e7b7211c5d55f3badf9e0df2

# Upstream's compose file uses three volumes. A Railway service has one, so
# all three state directories live under /data (the template's volume).
# Telemetry is off unless you set QWENPAW_TELEMETRY_DISABLED=false.
ENV QWENPAW_WORKING_DIR=/data/working \
    QWENPAW_SECRET_DIR=/data/working.secret \
    QWENPAW_BACKUP_DIR=/data/working.backups \
    QWENPAW_AGENT_LANGUAGE=en \
    QWENPAW_TELEMETRY_DISABLED=true \
    QWENPAW_CHANNEL_PRESET=light \
    QWENPAW_RUNNING_IN_CONTAINER=1 \
    QWENPAW_TRUSTED_PROXIES=10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,fd00::/8 \
    MALLOC_ARENA_MAX=2 \
    PYTHONUNBUFFERED=1 \
    PORT=8088

COPY --chmod=0755 railway/start.sh /railway/start.sh
COPY --chmod=0644 railway/setup.py /railway/setup.py

# Fail the build, not the first boot, if an upstream helper we use is gone.
RUN sh -n /railway/start.sh \
 && /app/venv/bin/python -m py_compile /railway/setup.py \
 && QWENPAW_WORKING_DIR=/tmp/qp QWENPAW_SECRET_DIR=/tmp/qp.secret /app/venv/bin/python -c \
    "from qwenpaw.app.auth import _hash_password, _load_auth_data, _save_auth_data, verify_password" \
 && command -v qwenpaw flock >/dev/null \
 && (rm -r /tmp/qp /tmp/qp.secret 2>/dev/null || true)

EXPOSE 8088
ENTRYPOINT []
CMD ["/railway/start.sh"]
