# Glumoo INS migration

## Goal
Move the Glumoo Instagram daily generation workflow to another OpenClaw host with minimal setup.

## Minimum requirement
The target host only needs:
- this `skills/glumoo-ins/` folder
- the `nano-banana-pro` skill installed in OpenClaw
- a working Yunwu/Gemini-compatible image API key via `XHS_IMAGE_API_KEY` (preferred) or `GOOGLE_API_KEY` / `GEMINI_API_KEY`

Optional but recommended configuration is now done via environment variables, so the skill can be moved without editing the script.

## What to copy
Copy this whole folder:

```text
skills/glumoo-ins/
```

Important files:
- `SKILL.md`
- `ins.py`
- `references/SOP.md`
- `references/MIGRATION.md`
- `references/CONFIG.md`

## Environment variables
Set one of these on the target machine:
- `GOOGLE_API_KEY`
- `GEMINI_API_KEY`

If both exist, current behavior prefers `GOOGLE_API_KEY`.

## Path assumptions in ins.py
Current script assumes these paths exist:
- workspace: `/Users/Apple/.openclaw/workspace-ins`
- mirror root: `/Users/Apple/Documents/Glumoo/02_每日内容生成`

Product reference root no longer needs an external local Glumoo folder by default.
It now defaults to the packaged asset folder inside this skill:
- `skills/glumoo-ins/assets/product_refs/`

On another host, you usually only need to set these environment variables if desired:
1. `GLUMOO_WORKSPACE`
2. `GLUMOO_MIRROR_ROOT`
3. `GLUMOO_SEND_ROOT`
4. `GLUMOO_TELEGRAM_CHAT` (if using `--send`)
5. `GLUMOO_REF_DIR` (only if not using packaged refs)

## Product assets expected
This portable package already includes product reference files under:
- `skills/glumoo-ins/assets/product_refs/sku1.png`
- `skills/glumoo-ins/assets/product_refs/sku2.jpg`
- `skills/glumoo-ins/assets/product_refs/sku3.jpg`

If you keep the package structure unchanged, you can point `REF_DIR` to this local assets folder and do not need to prepare product images separately.

## State file
Product rotation state is stored in:
- `.ins_sku_state`

If migrating fresh, it is safe to delete/reset this file and start from product 1.

## Test command
Minimal first test:

```bash
python3 skills/glumoo-ins/ins.py --date 2026-03-13
```

Example with environment variables:

```bash
export GOOGLE_API_KEY=REDACTED_FOR_GITHUB
export GLUMOO_WORKSPACE="$HOME/.openclaw/workspace-ins"
export GLUMOO_MIRROR_ROOT="$HOME/Documents/Glumoo/02_每日内容生成"
python3 skills/glumoo-ins/ins.py --date 2026-03-13
```

If you want Telegram delivery too:

```bash
export GLUMOO_TELEGRAM_CHAT="telegram:-100xxxx"
python3 skills/glumoo-ins/ins.py --date 2026-03-13 --send
```

Then verify:
- `caption.md` exists
- `meta.json` exists
- `p1.png` to `p4.png` exist
- hashtags include `#Glumoo` and `#NAGlumoo`
- at least one image clearly shows the product

## Optional adaptation
If the target OpenClaw should not send to Telegram, either:
- do not pass `--send`, or
- change/remove `TELEGRAM_CHAT` and `send_to_telegram()` behavior in `ins.py`

## Packaging suggestion
For transfer, package the folder as:

```bash
tar -czf glumoo-ins-portable.tar.gz skills/glumoo-ins
```

or zip it.
hange/remove `TELEGRAM_CHAT` and `send_to_telegram()` behavior in `ins.py`

## Packaging suggestion
For transfer, package the folder as:

```bash
tar -czf glumoo-ins-portable.tar.gz skills/glumoo-ins
```

or zip it.
behavior in `ins.py`

## Packaging suggestion
For transfer, package the folder as:

```bash
tar -czf glumoo-ins-portable.tar.gz skills/glumoo-ins
```

or zip it.
