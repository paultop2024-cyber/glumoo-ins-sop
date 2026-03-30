# Glumoo INS SOP Skill

Portable Glumoo Instagram daily asset generator for OpenClaw.

This repository packages the Glumoo INS workflow as a reusable skill, including the generator, SOP, migration notes, config references, and product reference assets.

## What it does
- Generates a daily Instagram review pack
- Produces a 4-image 4:5 carousel by default
- Writes `caption.md` and `meta.json`
- Applies product rotation logic (`1 -> 2 -> 3`)
- Uses Malaysia / Kuala Lumpur premium pet-lifestyle positioning
- Supports Telegram review delivery in the workflow
- Mirrors outputs into the business content folder

## Current scope
- Image posts only
- Carousel-first workflow
- No Reels / video automation in this package
- Review-pack workflow, not direct Instagram auto-publishing

## Output bundle
Each successful daily run produces:
- `caption.md`
- `meta.json`
- `p1.png`
- `p2.png`
- `p3.png`
- `p4.png`

## Key files
- `SKILL.md` — skill contract and usage guidance
- `ins.py` — executable generator
- `references/SOP.md` — durable SOP and output rules
- `references/MIGRATION.md` — migration checklist for another OpenClaw host
- `references/CONFIG.md` — paths, state, and environment expectations
- `.env.example` — environment variable template

## Quick start
1. Put this folder under `skills/glumoo-ins/`
2. Configure environment variables from `.env.example`
3. Ensure Python 3 is available
4. Run:

```bash
python3 skills/glumoo-ins/ins.py --date YYYY-MM-DD --send
```

Use `--advance-state` when you want to move the product rotation forward after a successful run.

## Guardrails
- Never use `sku` in user-facing copy
- Always include `#Glumoo` and `#NAGlumoo`
- Keep the pet visually consistent across the carousel
- Keep product visibility strong when required
- Maintain premium Malaysian residential lifestyle cues
- Avoid medical, cure, or guarantee claims

## Notes
- This repository is intentionally published with workflow logic preserved.
- Sensitive API values are not included.
- `.env.example` is kept as a template for setup.
