[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/qwenpaw-3?utm_medium=integration&utm_source=button&utm_campaign=qwenpaw)

# QwenPaw on Railway

This repo packages [QwenPaw](https://github.com/agentscope-ai/QwenPaw) **v2.3.0.post1** as a one-click Railway template. QwenPaw is AgentScope's open-source personal AI assistant: a web console for chatting with your agents, plus long-term memory, skills, scheduled tasks, MCP tools and chat channels (Telegram, Discord, Slack, DingTalk, Feishu, QQ and more). It is Apache-2.0 licensed.

The service builds from this repo's `Dockerfile`, which pins the official image `agentscope/qwenpaw:v2.3.0.post1` by version **and** digest (`sha256:033d3088…0df2`).

## What it deploys

| Service | Source | Role | Storage |
| --- | --- | --- | --- |
| **QwenPaw** (public) | this repo, `Dockerfile` | Web console and API on Railway's `PORT` (8088) | Volume at `/data` |

Everything QwenPaw keeps lives on the volume: `/data/working` (config, agents, chats, memory, skills), `/data/working.secret` (login, encrypted provider API keys and the key that decrypts them) and `/data/working.backups` (backups made in the console). Upstream's Compose file uses three volumes for these; a Railway service has one, so they share it.

## Variables

The deploy form asks for nothing. The template sets:

| Variable | Default | What it does |
| --- | --- | --- |
| `QWENPAW_AUTH_USERNAME` | `paw-` + 10 random characters | Console login name. Random on purpose: five wrong passwords lock a name for 15 minutes. |
| `QWENPAW_AUTH_PASSWORD` | 32 random characters | Console password. |
| `PORT` | `8088` | Port the console listens on (the public domain targets it). |

Find the login in Railway: **QwenPaw service → Variables**. Change either variable and redeploy to reset the login (old sessions are signed out). A password you change inside the console is kept until one of the two variables changes.

Optional, set them on the service if you need them: `QWENPAW_AGENT_LANGUAGE` (`en` default; `zh`, `ru` or `id`, read on the first boot only), `QWENPAW_LOG_LEVEL` (`info`), `QWENPAW_TELEMETRY_DISABLED` (`true` here; upstream's default is on).

## After you deploy

1. Open the service's public URL and sign in with the username and password from the Variables tab.
2. Chat right away: QwenPaw v2.3 answers out of the box with upstream's default free model (Kilo's `kilo-auto/free`, rate-limited and run by a third party). For your own models, go to **Settings → Models**, pick a provider (OpenAI, Anthropic, Gemini, DashScope/Qwen, DeepSeek, OpenRouter, Ollama on another host, …), paste your API key and choose the default model. Keys are stored encrypted on the volume.
3. Chat in the console, or connect a channel under **Channels** (for example a Telegram bot token).

## How this differs from upstream's Docker image

The image is upstream's, unchanged. `railway/start.sh` replaces upstream's entrypoint:

- **Smaller.** Upstream starts the app under supervisord next to a full Xfce desktop on a virtual display (about 510 MB at idle). On a Linux server QwenPaw's browser runs headless and desktop control isn't supported, so the template runs only the app: about 0.4 GB at idle instead of 0.5+, healthy about 15 seconds after start.
- **Login always on.** `QWENPAW_AUTH_ENABLED` is forced to `true` and the account is created from the variables before the app starts (`railway/setup.py`). Without a usable login the container stops instead of serving an open console.
- **English persona files.** Upstream's `qwenpaw init --defaults` writes the agent's persona files (`AGENTS.md`, `SOUL.md`, …) in Chinese. The template writes the agent language into `config.json` first.
- **Real client IPs.** Railway's private ranges are set as `security.trusted_proxies`, so the login rate limiter sees the visitor's IP, not the proxy's.
- **Restarts that work on every plan.** Any stop Railway didn't ask for (crash, out-of-memory, an in-app restart) exits non-zero, so the `ON_FAILURE` restart policy brings it back.
- **Telemetry off** by default.

Health check: `/api/version` (answers without login). Restart policy: on failure, 10 retries.

## Resources

Measured on Railway with v2.3.0.post1:

| Use | RAM |
| --- | --- |
| Console idle, chat, memory, skills, channels | about 0.4 GB |
| Agent using its browser tool (headless Chromium) | about 0.9 GB |
| Local models (QwenPaw Local / llama.cpp) | 2 GB or more, depending on the model |

On Railway's Free and Trial plans (0.5 GB per service) the console and chat work, but a browser task gets the service killed for memory. The container then exits non-zero, Railway restarts it within seconds and your data stays on the volume, but that reply is lost. If you want the browser tool, give the service at least 1 GB (**Settings → Resources**).

## Updates

Deployers get Railway's "update available" notice when this repo's `main` branch changes. Each version bump changes the pinned tag and digest in `Dockerfile` and adds an entry to [`CHANGELOG.md`](CHANGELOG.md), breaking changes first. Read it before you apply an update. Your data stays on the volume across updates; download a backup from the console first if you want one off Railway.

## Licence

The wrapper files in this repo are MIT. QwenPaw itself is Apache-2.0, © AgentScope.
