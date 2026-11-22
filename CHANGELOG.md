# Changelog

## 2026-11-22: QwenPaw v2.3.0.post1 (first release)

- Official image `agentscope/qwenpaw:v2.3.0.post1@sha256:033d30887bbb5563ee8ed20a43073ddd7ee93290e7b7211c5d55f3badf9e0df2`.
- One service with a volume at `/data` for the working, secret and backup directories.
- Console login created from generated variables on first boot, always on.
- App runs without upstream's desktop helpers (Xvfb, Xfce): about 0.4 GB RAM at idle on Railway (the browser tool needs about 0.9 GB).
- Persona files in English by default (`QWENPAW_AGENT_LANGUAGE`).
- Railway's private ranges trusted as proxies; unexpected stops exit non-zero so Railway restarts the service.
