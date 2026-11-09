# hermes-deepseek-quota

Chip kecil di **status bar bawah** Hermes desktop yang tunjuk baki DeepSeek, supaya tak terkejut bila token habis.

```
▬ $5.70        ← bar = baki berbanding puncak top-up terakhir
```

- **Hover** → `DeepSeek: $5.70 baki · ≈595M token tinggal · guna hari ni $0.03 · 7 hari $0.31`
- **Klik** → refresh terus + toast ringkas
- Auto-refresh setiap **60 saat**; bila API gagal, chip jadi `—`

## Apa yang ia buat

| Bahagian | Fail | Kerja |
|---|---|---|
| Chip UI | `desktop/plugin.js` | Status-bar chip: pill bar + baki dolar, hover tooltip, klik refresh |
| Backend | `dashboard/plugin_api.py` | `GET /balance`: baca baki dari `api.deepseek.com/user/balance` + sejarah token/kos 7 hari dari `~/.hermes/state.db`, kira anggaran token tinggal pada kadar campuran sebenar kau |
| Manifest | `plugin.yaml`, `dashboard/manifest.json`, `__init__.py` | Daftar plugin; `__init__.py` wajib ada walaupun tiada tool |

**API key tak pernah masuk renderer** — chip cuma terima JSON (baki, token, kos). Key dibaca backend dari `~/.hermes/.env` (`DEEPSEEK_API_KEY`).

`tokens tinggal` = anggaran: `baki ÷ kadar $/1M token kau 7 hari lepas`. Sebab majoriti token kau cache-hit (murah), angka token nampak besar; context baru tanpa cache akan makan baki jauh lebih cepat.

## Pasang

Syarat: Hermes desktop dah dipasang, dan `DEEPSEEK_API_KEY` ada dalam `~/.hermes/.env`.

```bash
git clone https://github.com/amiramirul/hermes-deepseek-quota.git
cd hermes-deepseek-quota
./install.sh
```

Chip muncul dalam beberapa saat. Kalau tak muncul: **⌘K → Reload desktop plugins**.

Semak backend terus (tanpa app) — guna python Hermes:

```bash
~/.hermes/installs/*/environments/*/venv/bin/python3 - <<'PY'
import sys, json; sys.path.insert(0, __import__('os').path.expanduser('~/.hermes/plugins/deepseek-quota/dashboard'))
import plugin_api; print(json.dumps(plugin_api._collect(), indent=1))
PY
```

## Selepas format / mesin baru

1. Pasang Hermes + masukkan `DEEPSEEK_API_KEY` dalam `~/.hermes/.env`
2. `git clone` repo ni (private — login `amiramirul`)
3. `./install.sh`

Setel. Tiada config lain yang perlu diubah; `install.sh` yang jalankan `hermes plugins enable deepseek-quota`.

## Buang

```bash
./install.sh --remove
```

## Kemas kini

Edit fail dalam repo, kemudian `./install.sh` semula (ia salin ganti kedua-dua bahagian). Fail `state.json` (puncak baki) dicipta runtime dalam `~/.hermes/plugins/deepseek-quota/` — bukan dalam repo.

## Nota teknikal (untuk kali seterusnya)

- Plugin pakej **wajib** ada `__init__.py`, kalau tak: `Failed to load plugin: No __init__.py` dan route backend tak mount.
- Kelas Tailwind arbitrary (`h-[4px]`, `w-[32px]`) **tak wujud** untuk `plugin.js` — CSS app dicompile dari source sendiri. Guna inline `style={{}}` untuk geometri.
- `host.notify` kind yang sah: `info`, `success`, `error`, `warning` (bukan `warn`).
