# Glumoo INS config notes

## Core constants in ins.py
- `WORKSPACE`
- `SKILL_DIR`
- `OUT_ROOT`
- `SEND_ROOT`
- `MIRROR_ROOT`
- `STATE_FILE`
- `REF_DIR`
- `NANO_BANANA`
- `TELEGRAM_CHAT`

## Environment variable overrides
- `GLUMOO_WORKSPACE`
- `GLUMOO_OUT_ROOT`
- `GLUMOO_SEND_ROOT`
- `GLUMOO_MIRROR_ROOT`
- `GLUMOO_STATE_FILE`
- `GLUMOO_REF_DIR`
- `GLUMOO_NANO_BANANA`
- `GLUMOO_TELEGRAM_CHAT`

## Current behavior
- output root: `out/daily/YYYY-MM-DD/`
- send copy root: `/Users/Apple/.openclaw/workspace/out/ins_daily/YYYY-MM-DD/`
- mirror root: `/Users/Apple/Documents/Glumoo/02_每日内容生成/YYYY-MM-DD/ins/`
- default product refs: `skills/glumoo-ins/assets/product_refs/`
- product rotation: `1 -> 2 -> 3`
- supported args: `--date`, `--advance-state`, `--send`

## Required product mapping
Current mapping in `product_info()`:
- 1 -> `sku1.png`
- 2 -> `sku2.jpg`
- 3 -> `sku3.jpg`

Portable asset copy included in this skill:
- `assets/product_refs/sku1.png`
- `assets/product_refs/sku2.jpg`
- `assets/product_refs/sku3.jpg`

## Current quality expectations
- caption must not contain `sku`
- fixed hashtags must include `#Glumoo` and `#NAGlumoo`
- 4 images required
- all images 4:5
- same dog anchored across the set
- p2 should be the strongest product-visibility frame

## If adapting to another brand
Change these first:
- `BASE_HASHTAGS`
- `THEMES`
- `product_info()` mapping
- caption structure in `build_plan()`
- prompt structure in `build_plan()` and `generate_images()`
