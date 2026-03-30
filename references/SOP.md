# Glumoo Instagram SOP v1

## Goal
Build a stable daily Instagram image-post workflow for Glumoo.

This SOP is for image-first posting only:
- Carousel posts are the default
- Single-image posts are allowed when needed
- No Reels/video in this phase

Every daily output must produce:
- 1 final caption in `caption.md`
- 1 hashtag set in `caption.md`
- 4 images in 4:5 ratio
- A structured metadata file `meta.json`

## Brand Positioning
Glumoo is positioned as a premium Malaysia pet wellness and lifestyle brand.

Tone:
- English-first
- Can include a light amount of Malaysia-friendly phrasing or small Chinese/Manglish touches when natural
- Warm, premium, calm, credible
- Lifestyle-first, not hard-sell

Avoid:
- Mainland ecommerce tone
- Overclaiming
- Medical promises
- Pushy CTA language
- Generic AI-sounding copy

## Content Scope
Current focus is image posts only.

Primary format:
- 4-image carousel

Optional format:
- single-image post

Default assumption unless otherwise specified:
- 4-image carousel

## SKU Rotation
Rotate products in this order:
- 1 -> 2 -> 3 -> repeat

Rules:
- Maintain state in `.ins_sku_state`
- Do not mention the word `sku` in user-facing copy
- Use product naming naturally

## Daily Deliverables
For each date, create output under:
- `/Users/Apple/.openclaw/workspace-ins/out/daily/YYYY-MM-DD/`

Required files:
- `caption.md`
- `p1.png`
- `p2.png`
- `p3.png`
- `p4.png`
- `meta.json`

Mirror target after successful generation:
- `/Users/Apple/Documents/Glumoo/02_每日内容生成/YYYY-MM-DD/ins/`

## Content Structure
Each daily carousel should follow this intent:
- `p1`: strong hook / hero image
- `p2`: daily lifestyle scene with product naturally present when appropriate
- `p3`: trust / comfort / emotional reassurance
- `p4`: routine / feeding / simple CTA mood

All images must be:
- dog-only unless explicitly changed later
- 4:5 ratio
- premium lifestyle look
- consistent in tone and visual world
- free of readable text on-image unless explicitly required

## Visual Direction
Use a premium, clean, modern visual language.

Preferred scenes:
- condo living spaces
- bright modern interiors
- soft outdoor park or walking scenes
- daily pet-care routines

Avoid:
- cluttered backgrounds
- cheap ad look
- unrealistic packaging placement
- excessive props
- text-heavy visuals

## Caption Rules
Caption must:
- feel premium and natural
- start from a lifestyle or pet-parent reality
- not sound like a product listing
- keep CTA soft and credible

Recommended shape:
1. Hook / relatable scene
2. Problem or emotional truth
3. Gentle product integration
4. Soft CTA
5. Hashtags

Hashtag rules:
- about 10-15 total
- always include fixed brand hashtags `#Glumoo` and `#NAGlumoo`
- combine brand + category + local relevance + caption-related dynamic tags
- avoid a fully static hashtag block
- no spammy stuffing

## Image Generation Rules
Use the existing local image workflow where possible.

Image requirements:
- 4 images per daily run
- 4:5 ratio
- all-dog style
- premium commercial pet lifestyle photography
- no watermark
- no added random logos
- no readable text on image

If a product pack appears:
- use the correct reference image for the current product
- preserve packaging shape/color consistency
- integrate naturally into the scene

## Execution Order
Daily execution order must be:
1. Determine date
2. Determine next product by rotation state
3. Build theme/copy direction for today
4. Generate caption
5. Generate 4 images
6. Save files to workspace daily folder
7. Mirror to Glumoo content folder
8. Optionally deliver to chat only if the current automation is enabled

## Quality Gate
Before considering a run successful, verify:
- all 4 image files exist
- `caption.md` exists and is not empty
- copy does not contain `sku`
- images are 4:5 workflow outputs
- output folder includes current date
- metadata records product number and generation timestamp

## Automation Intent
The automation should follow this SOP every day instead of improvising from a short prompt.

This means:
- the agent/job should reference this SOP
- the generator logic should create the fixed daily file bundle
- the daily job prompt should be explicit about these constraints

## Current Phase Boundary
In this phase, do not add:
- Reels
- video scripts
- voiceover logic
- publishing automation to Instagram itself

Current target is reliable daily generation of image-post assets only.
