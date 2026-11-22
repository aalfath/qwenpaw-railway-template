"""Boot-time setup for QwenPaw on Railway (run by start.sh before the app).

1. First boot (no config.json on the volume): seed the agent language, then
   run upstream's own non-interactive `qwenpaw init --defaults
   --accept-security` (what upstream's Docker entrypoint runs).
2. security.trusted_proxies in config.json from QWENPAW_TRUSTED_PROXIES, so
   the login rate limiter sees the real client IP behind Railway's proxy.
3. The single console login from QWENPAW_AUTH_USERNAME/QWENPAW_AUTH_PASSWORD:
   created on first boot, and applied again only when one of the two
   variables changed since the last boot (a password changed in the Console
   is kept until then). Exits non-zero without a usable login, so the
   console is never reachable without one.
"""
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

MIN_PASSWORD = 12
LANGS = ("en", "zh", "ru", "id")


def log(msg):
    print(f"[railway] {msg}", file=sys.stderr, flush=True)


def fail(msg):
    log(f"FATAL: {msg}")
    sys.exit(1)


def write_json(path, data, mode=0o600):
    path = Path(path)
    if path.exists():
        mode = path.stat().st_mode & 0o777
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def first_boot(work):
    cfg = work / "config.json"
    if cfg.exists():
        return
    lang = os.environ.get("QWENPAW_AGENT_LANGUAGE", "en").strip().lower() or "en"
    if lang not in LANGS:
        log(f"QWENPAW_AGENT_LANGUAGE '{lang}' not supported; using 'en'")
        lang = "en"
    log(f"first boot: initialising {work} (agent language {lang})")
    write_json(cfg, {"agents": {"language": lang}}, 0o644)
    rc = subprocess.run(["qwenpaw", "init", "--defaults", "--accept-security"],
                        stdin=subprocess.DEVNULL, timeout=600).returncode
    if rc != 0:
        cfg.unlink(missing_ok=True)
        fail(f"qwenpaw init exited with {rc}")
    agent = work / "workspaces" / "default" / "agent.json"
    if agent.exists():
        data = json.loads(agent.read_text(encoding="utf-8"))
        if data.get("language") != lang:
            data["language"] = lang
            write_json(agent, data)
    log("first boot: initialisation complete")


def trusted_proxies(work):
    raw = os.environ.get("QWENPAW_TRUSTED_PROXIES", "")
    wanted = [p.strip() for p in raw.split(",") if p.strip()]
    cfg_path = work / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    sec = cfg.setdefault("security", {})
    if sec.get("trusted_proxies") != wanted:
        sec["trusted_proxies"] = wanted
        write_json(cfg_path, cfg, 0o644)
        log(f"security.trusted_proxies set to {wanted}")


def login(secret_dir):
    from qwenpaw.app.auth import _hash_password, _load_auth_data, _save_auth_data

    user = os.environ.get("QWENPAW_AUTH_USERNAME", "").strip()
    pw = os.environ.get("QWENPAW_AUTH_PASSWORD", "").strip()
    if not user:
        fail("QWENPAW_AUTH_USERNAME is empty; the console must not run without a login")
    if len(pw) < MIN_PASSWORD:
        fail(f"QWENPAW_AUTH_PASSWORD must be at least {MIN_PASSWORD} characters")

    state_path = secret_dir / "railway-login-state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    salt = state.get("salt") or secrets.token_hex(16)
    digest = hmac.new(salt.encode(), f"{user}\0{pw}".encode(), hashlib.sha256).hexdigest()

    data = _load_auth_data()
    if data.get("_auth_load_error"):
        fail("auth.json on the volume is unreadable")
    current = data.get("user")
    if current and state.get("digest") == digest:
        log(f"login '{current.get('username')}' unchanged")
        return
    pw_hash, pw_salt = _hash_password(pw)
    data["user"] = {"username": user, "password_hash": pw_hash, "password_salt": pw_salt}
    # A new jwt_secret signs out every old session when the login changes.
    data["jwt_secret"] = secrets.token_hex(32)
    _save_auth_data(data)
    write_json(state_path, {"salt": salt, "digest": digest})
    log(("login updated from variables: '%s'" if current else "login created: '%s'") % user)


def main():
    work = Path(os.environ["QWENPAW_WORKING_DIR"])
    secret_dir = Path(os.environ["QWENPAW_SECRET_DIR"])
    first_boot(work)
    trusted_proxies(work)
    login(secret_dir)


if __name__ == "__main__":
    main()
