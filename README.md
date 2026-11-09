# DeepSeek Quota — a balance chip for the Hermes desktop status bar

A small status-bar chip for [Hermes Agent](https://hermes-agent.nousresearch.com/)'s desktop app that
shows your **DeepSeek API balance** and the **estimated tokens left**, so running out never comes as
a surprise.

```
▬ $5.69          ← pill bar (share of your last top-up) + balance
```

![The chip in the Hermes status bar](docs/chip.png)

- **Hover** → `DeepSeek: $5.69 left · ≈594M tokens left · today $0.03 · 7d $0.31`
- **Click** → refresh now, plus a short toast with the same numbers
- Refreshes every **60 seconds**; when the API call fails the chip shows `—`

The plumbing isn't DeepSeek-specific — point `BALANCE_URL` in `dashboard/plugin_api.py` at another
provider that exposes an account balance and the same chip reports that instead.

## Install

Requirements: the Hermes **desktop** app (the chip needs a status bar — the CLI/gateway alone has
none) and a DeepSeek key in `~/.hermes/.env`.

```bash
git clone https://github.com/amiramirul/hermes-deepseek-quota.git
cd hermes-deepseek-quota
./install.sh
```

The chip appears within a few seconds. If it doesn't: **⌘K → Reload desktop plugins**.

Add the key if you haven't already:

```bash
printf 'DEEPSEEK_API_KEY=%s\n' 'sk-…' >> ~/.hermes/.env
```

No script? Copy the two halves yourself:

```bash
H=${HERMES_HOME:-$HOME/.hermes}
mkdir -p "$H/plugins/deepseek-quota/dashboard" "$H/desktop-plugins/deepseek-quota"
cp plugin.yaml __init__.py "$H/plugins/deepseek-quota/"
cp dashboard/manifest.json dashboard/plugin_api.py "$H/plugins/deepseek-quota/dashboard/"
cp desktop/plugin.js "$H/desktop-plugins/deepseek-quota/plugin.js"
hermes plugins enable deepseek-quota
```

## How it works

| Part | File | Role |
|---|---|---|
| Chip UI | `desktop/plugin.js` | Status-bar chip: pill bar + balance, hover detail, click-to-refresh. Polls `ctx.rest('/balance')`. |
| Backend | `dashboard/plugin_api.py` | `GET /balance` — reads `api.deepseek.com/user/balance` plus the profile's last 7 days of token/cost history from `$HERMES_HOME/state.db`, and returns balance, estimated tokens left and today's spend. Results cached 45 s. |
| Package | `plugin.yaml`, `__init__.py`, `dashboard/manifest.json` | Registers the plugin so the backend route mounts. `__init__.py` is required even though the plugin registers no tools. |

**The API key never reaches the renderer.** The backend reads `DEEPSEEK_API_KEY` from the profile
`.env` (or the process environment); the chip only ever receives numbers.

### How "tokens left" is estimated

`balance ÷ your blended rate ($ per 1M tokens, measured over the last 7 days of local sessions)`.

The blend comes from your own usage mix, and the mix matters a lot: cached-context reads are roughly
50× cheaper than fresh input, so a cache-heavy week makes the token estimate look huge while a fresh
conversation burns the same balance far faster. With no local history yet, the fallback blend is
`90% cache-read + 5% input + 5% output` at DeepSeek Flash pricing.

The **bar** is the balance relative to the highest balance seen since install — 100% right after a
top-up, draining as you spend. That peak lives in
`$HERMES_HOME/plugins/deepseek-quota/state.json` (created at runtime, never committed).

### Tested on

- Hermes Agent 0.22.5 (desktop plugin SDK: `statusBar.right`, `ctx.rest`, `useQuery`)
- macOS; should work anywhere the Electron desktop app runs
- Python side needs nothing beyond what Hermes already ships (stdlib + FastAPI)

## Troubleshooting

| Symptom | Cause |
|---|---|
| Chip shows `—` | Key missing from `.env`, or the backend route isn't mounted — check `hermes plugins list` shows `deepseek-quota` enabled |
| `Failed to load plugin 'deepseek-quota': No __init__.py` | The package root lost its `__init__.py`. Copy it back. |
| Chip missing entirely | ⌘K → **Reload desktop plugins**; confirm Settings → Plugins lists it and it's on |
| Bar invisible / zero height | Tailwind arbitrary classes (`h-[4px]`) are *not* compiled for `plugin.js`. Geometry has to be inline `style={{}}`. |
| Balance looks stale | 45 s server cache + 60 s poll; click the chip to force a refresh |

## New machine / restore

1. Install Hermes and put `DEEPSEEK_API_KEY` in `~/.hermes/.env`
2. `git clone https://github.com/amiramirul/hermes-deepseek-quota.git`
3. `cd hermes-deepseek-quota && ./install.sh`

Nothing else to configure — `install.sh` runs `hermes plugins enable deepseek-quota` for you.

## Update / uninstall

```bash
git pull && ./install.sh     # update the installed copy
./install.sh --remove        # remove both halves and disable the plugin
```

## License

MIT — see [LICENSE](LICENSE).
