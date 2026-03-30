---
name: glumoo-ins
description: Portable Glumoo Instagram daily asset generator for OpenClaw. Use when generating the daily Glumoo Instagram package, rebuilding or migrating the Glumoo INS SOP to another OpenClaw, or packaging the workflow so another machine can run it with only a Gemini image API key. Produces caption.md, meta.json, and 4 carousel images with Malaysia/Kuala Lumpur premium pet-lifestyle positioning.
---

# Glumoo INS

Use this skill as the canonical, portable implementation of the Glumoo Instagram SOP.

## What this skill owns
- Daily Glumoo Instagram generation
- Product rotation state (`1 -> 2 -> 3`)
- Caption generation
- Hashtag generation
- 4-image carousel generation
- Telegram delivery of caption + images
- Mirroring outputs into the Glumoo content folder

## Portability goal
Make the workflow portable across OpenClaw installs.

A fresh OpenClaw should be able to run this skill after:
1. placing this skill folder under `skills/glumoo-ins/`
2. setting a Gemini image API key (`GOOGLE_API_KEY` or `GEMINI_API_KEY`)
3. optionally editing local paths in `ins.py` if the Glumoo asset folders differ

## Required runtime pieces
- Python 3
- `uv`
- the `nano-banana-pro` skill installed at the standard OpenClaw skill path
- a valid Yunwu/Gemini-compatible image API key in environment

## Files in this skill
- `ins.py` — executable generator
- `references/SOP.md` — durable SOP and output contract
- `references/MIGRATION.md` — migration checklist for another OpenClaw host
- `references/CONFIG.md` — paths, state, and environment variable expectations

Read the references only when needed.

## Default command
Run:

```bash
python3 skills/glumoo-ins/ins.py --date YYYY-MM-DD --send
```

Use `--advance-state` when the run should advance the product rotation after success.

## Output contract
Each daily run must produce:
- `caption.md`
- `meta.json`
- `p1.png`
- `p2.png`
- `p3.png`
- `p4.png`

## Guardrails
- Never let the caption contain `sku`
- Always include `#Glumoo` and `#NAGlumoo`
- Keep the dog consistent across the carousel
- Ensure at least one image clearly shows the product packaging
- Keep the visual language Malaysia / Kuala Lumpur / premium residential lifestyle

## Migration and packaging workflow
When the user asks to move this workflow to another OpenClaw:
1. Read `references/MIGRATION.md`
2. Normalize any hard-coded paths in `ins.py` if needed
3. Ensure the skill folder is self-contained
4. Package the folder as a transferable artifact (zip/tar.gz or skill package)
5. Provide the target machine with the minimal setup steps only

## Do not add here
- Extra README-style docs
- Instagram auto-publish claims unless actually implemented
- Facebook auto-publish claims unless actually implemented
r as a transferable artifact (zip/tar.gz or skill package)
5. Provide the target machine with the minimal setup steps only

## Do not add here
- Extra README-style docs
- Instagram auto-publish claims unless actually implemented
- Facebook auto-publish claims unless actually implemented
