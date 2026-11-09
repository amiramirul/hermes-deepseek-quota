"""DeepSeek quota backend — powers the `deepseek-quota` desktop status-bar chip.

Mounted at /api/plugins/deepseek-quota/ by the dashboard plugin system.

Routes
------
GET /balance
    Live DeepSeek balance (api.deepseek.com/user/balance) plus the profile's own
    local spend/token history from $HERMES_HOME/state.db, folded into an
    estimated "tokens left" figure at the user's real blended rate.

The API key never leaves this process: the chip receives numbers, never secrets.
Plugin contract: never raise out of a handler — every failure comes back as
{"ok": false, "error": "..."} so the chip can render a neutral state.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

PLUGIN_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PLUGIN_DIR / "state.json"
BALANCE_URL = "https://api.deepseek.com/user/balance"
CACHE_TTL = 45.0
# Fallback blended rate ($ per 1M context tokens) when there is no local history:
# 90% cache-read @0.003 + 5% input-miss @0.15 + 5% output @0.60 (deepseek-flash).
DEFAULT_RATE_PER_MTOK = 0.0402

_cache: dict[str, object] = {"at": 0.0, "payload": None}


def _hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    return Path.home() / ".hermes"


def _api_key() -> str | None:
    key = None
    try:  # gateway process: profile-scoped secret scope
        from agent.secret_scope import get_secret

        key = get_secret("DEEPSEEK_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        for env_path in (_hermes_home() / ".env", Path.home() / ".hermes" / ".env"):
            try:
                for line in env_path.read_text(errors="ignore").splitlines():
                    if line.startswith("DEEPSEEK_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            except Exception:
                pass
            if key:
                break
    return key or None


def _fetch_balance(key: str) -> dict:
    req = urllib.request.Request(
        BALANCE_URL,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def _spend_stats(days: int = 7) -> dict:
    """Local spend/token mix for the last N days, from the canonical session store."""
    db = _hermes_home() / "state.db"
    out = {"spent_7d": None, "spent_today": None, "tokens": 0, "mix": None}
    if not db.exists():
        return out
    since = time.time() - days * 86400
    local_midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)
    except Exception:
        return out
    try:
        row = con.execute(
            "SELECT COALESCE(SUM(estimated_cost_usd),0), "
            "COALESCE(SUM(input_tokens),0), COALESCE(SUM(cache_read_tokens),0), "
            "COALESCE(SUM(output_tokens),0) FROM sessions WHERE started_at >= ?",
            (since,),
        ).fetchone()
        spent_7d, miss, cached, out_tok = row
        today = con.execute(
            "SELECT COALESCE(SUM(estimated_cost_usd),0) FROM sessions WHERE started_at >= ?",
            (local_midnight.timestamp(),),
        ).fetchone()[0]
        out.update(
            spent_7d=round(float(spent_7d), 4),
            spent_today=round(float(today), 4),
            tokens=int(miss) + int(cached) + int(out_tok),
            mix={"miss": int(miss), "cache": int(cached), "out": int(out_tok)},
        )
    except Exception:
        pass
    finally:
        con.close()
    return out


def _peak(balance: float) -> float:
    """Highest balance seen since install — the bar's 100% mark (resets on top-up)."""
    data = {}
    try:
        data = json.loads(STATE_FILE.read_text())
    except Exception:
        data = {}
    peak = float(data.get("peak") or 0.0)
    if balance > peak:
        peak = balance
        try:
            STATE_FILE.write_text(json.dumps({"peak": round(peak, 2), "updated": time.time()}))
        except Exception:
            pass
    return peak or balance


def _collect() -> dict:
    payload: dict = {
        "ok": False,
        "currency": "USD",
        "balance": None,
        "peak": None,
        "tokens_left": None,
        "rate_per_mtok": DEFAULT_RATE_PER_MTOK,
        "spent_today": None,
        "spent_7d": None,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    key = _api_key()
    if not key:
        payload["error"] = "DEEPSEEK_API_KEY not found in .env"
        return payload

    try:
        body = _fetch_balance(key)
    except urllib.error.HTTPError as exc:
        payload["error"] = f"HTTP {exc.code} from api.deepseek.com"
        return payload
    except Exception as exc:  # network, DNS, timeout
        payload["error"] = f"network: {type(exc).__name__}"
        return payload

    infos = body.get("balance_infos") or []
    if not infos:
        payload["error"] = "no balance_infos in response"
        return payload
    info = next((i for i in infos if str(i.get("currency", "")).upper() == "USD"), infos[0])
    try:
        balance = float(info.get("total_balance") or 0.0)
    except Exception:
        payload["error"] = "unparseable total_balance"
        return payload

    stats = _spend_stats()
    tokens = stats.get("tokens") or 0
    spent = stats.get("spent_7d") or 0.0
    rate = DEFAULT_RATE_PER_MTOK
    if tokens > 0 and spent > 0:
        rate = spent / (tokens / 1_000_000.0)

    payload.update(
        ok=True,
        currency=str(info.get("currency") or "USD"),
        balance=round(balance, 2),
        granted=float(info.get("granted_balance") or 0.0),
        topped_up=float(info.get("topped_up_balance") or 0.0),
        available=bool(body.get("is_available", True)),
        peak=round(_peak(balance), 2),
        rate_per_mtok=round(rate, 6),
        tokens_left=int(balance / rate * 1_000_000.0) if rate > 0 else None,
        spent_today=stats.get("spent_today"),
        spent_7d=stats.get("spent_7d"),
        local_tokens_7d=tokens,
    )
    return payload


@router.get("/balance")
async def balance(refresh: bool = False):
    now = time.time()
    if not refresh and _cache["payload"] and now - float(_cache["at"]) < CACHE_TTL:
        return _cache["payload"]
    payload = _collect()
    _cache.update(at=now, payload=payload)
    return payload
