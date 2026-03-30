#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(os.getenv("GLUMOO_WORKSPACE", "/Users/Apple/.openclaw/workspace-ins"))
OUT_ROOT = Path(os.getenv("GLUMOO_OUT_ROOT", str(WORKSPACE / "out" / "daily")))
SEND_ROOT = Path(os.getenv("GLUMOO_SEND_ROOT", "/Users/Apple/.openclaw/workspace/out/ins_daily"))
MIRROR_ROOT = Path(os.getenv("GLUMOO_MIRROR_ROOT", "/Users/Apple/Documents/Glumoo/02_每日内容生成"))
STATE_FILE = Path(os.getenv("GLUMOO_STATE_FILE", str(WORKSPACE / ".ins_sku_state")))
REF_DIR = Path(os.getenv("GLUMOO_REF_DIR", str(SKILL_DIR / "assets" / "product_refs")))
NANO_BANANA = Path(os.getenv("GLUMOO_NANO_BANANA", "/Users/Apple/.openclaw/skills/nano-banana-pro-1.0.1/scripts/generate_image.py"))
TELEGRAM_CHAT = os.getenv("GLUMOO_TELEGRAM_CHAT", "telegram:-1003790450037")

# Keep INS SOP aligned with the XHS SOP provider contract.
# Current INS flow actively uses the image side; text side is reserved for caption/copy model upgrades.
XHS_TEXT_API_KEY =REDACTED_FOR_GITHUB
XHS_TEXT_BASE_URL = os.getenv("XHS_TEXT_BASE_URL") or os.getenv("GEMINI_BASE_URL") or os.getenv("GOOGLE_GENAI_BASE_URL")
XHS_TEXT_MODEL = os.getenv("XHS_TEXT_MODEL") or "models/gemini-3.1-flash-lite-preview"
XHS_IMAGE_API_KEY =REDACTED_FOR_GITHUB
XHS_IMAGE_BASE_URL = os.getenv("XHS_IMAGE_BASE_URL") or os.getenv("GEMINI_BASE_URL") or os.getenv("GOOGLE_GENAI_BASE_URL")
XHS_IMAGE_MODEL = os.getenv("XHS_IMAGE_MODEL") or os.getenv("GEMINI_IMAGE_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-image-preview"
XHS_IMAGE_ASPECT_RATIO = os.getenv("XHS_IMAGE_ASPECT_RATIO") or "4:5"


@dataclass
class DailyPlan:
    product_id: int
    product_name: str
    ref_image: str | None
    theme_key: str
    theme_label: str
    caption: str
    hashtags: list[str]
    image_prompts: list[str]


THEMES = [
    {
        "key": "kl-morning-routine",
        "label": "KL Morning Wellness Routine",
        "opener": "Some of the best pet routines in Kuala Lumpur start quietly - a slow morning, soft light, and a little consistency.",
        "body": "For pet parents living between condo mornings, weekend park walks, and busy city schedules, wellness works best when it feels easy to keep up with.",
        "cta": "Save this for your next pawrent routine reset, or DM us \"guide\" if you want help choosing the right fit.",
        "scene": "upscale Kuala Lumpur condo morning routine",
    },
    {
        "key": "park-lifestyle",
        "label": "Premium Parkside Pawrent Lifestyle",
        "opener": "A good pet routine should feel as natural as your weekend walk downstairs to the park.",
        "body": "In premium neighbourhoods around KL, the little things matter - clean routines, calmer feeding moments, and wellness habits that fit beautifully into daily life.",
        "cta": "Send this to a fellow pawrent, or DM us \"INFO\" if your furkid needs a gentler daily routine.",
        "scene": "high-end residential park in Kuala Lumpur",
    },
    {
        "key": "senior-comfort-kl",
        "label": "Senior Comfort in a KL Community",
        "opener": "When dogs get older, comfort becomes part of the luxury too.",
        "body": "Think slower walks through a shaded community park, warm afternoons in a modern Malaysian home, and routines that support everyday ease without feeling complicated.",
        "cta": "Comment \"guide\" if you want the calm daily routine version for your furkid.",
        "scene": "shaded upscale KL community with tropical landscaping",
    },
    {
        "key": "terrace-home-living",
        "label": "Modern Terrace House Pet Routine",
        "opener": "The most beautiful pet routines are usually the ones that blend into home life without looking forced.",
        "body": "From terrace house mornings to relaxed evenings by the front lawn, pet wellness should feel premium, practical, and easy to repeat every day.",
        "cta": "DM us if you want help building a more premium routine for your furkid.",
        "scene": "modern Malaysian terrace house and front lawn",
    },
    {
        "key": "rainy-day-indoor",
        "label": "Rainy Day Indoor Comfort",
        "opener": "Not every good pet day needs sunshine - sometimes the nicest routines happen indoors while the rain rolls in outside.",
        "body": "KL weather shifts fast, so the best wellness habits are the ones that still feel calm and beautiful on rainy afternoons inside a bright, high-end home.",
        "cta": "Save this for your next rainy day routine, or DM us if your furkid does better with a calmer indoor rhythm.",
        "scene": "luxury Kuala Lumpur condo on a tropical rainy day",
    },
    {
        "key": "weekend-park-walk",
        "label": "Weekend Park Walk Energy",
        "opener": "Weekend dog energy hits different when the park is green, the light is soft, and the whole routine feels easy.",
        "body": "That premium KL pawrent feeling is not just about where you live - it is about building little routines that look good, feel calm, and fit real life.",
        "cta": "Send this to a weekend pawrent buddy, or DM us for a routine that fits park days and home days.",
        "scene": "weekend walk in a premium Kuala Lumpur park",
    },
    {
        "key": "city-pawrent-rhythm",
        "label": "City Pawrent Daily Rhythm",
        "opener": "City life gets busy, so pet wellness has to feel light, polished, and easy to keep going.",
        "body": "Between work, traffic, condo living, and quick park breaks, the routines that last are usually the ones that slide naturally into a premium urban lifestyle.",
        "cta": "Comment \"routine\" if you want the city pawrent version.",
        "scene": "premium urban pawrent life in Kuala Lumpur",
    },
]

BASE_HASHTAGS = [
    "#Glumoo",
    "#NAGlumoo",
    "#GlumooMY",
    "#PetWellness",
    "#HealthyPets",
    "#DailyPetRoutine",
    "#MalaysiaPets",
    "#KLPets",
    "#PetLifestyle",
    "#PremiumPetCare",
    "#PetParentsMY",
    "#PawrentsMY",
]

# Practical local pet mix for Malaysian Chinese urban households.
# This is an operating content roster for Glumoo generation, not a veterinary census.
DOG_TYPES = [
    {
        "key": "toy-poodle",
        "label": "Toy Poodle",
        "category": "dog",
        "scene_name": "toy poodle",
        "traits": "small elegant toy poodle, soft curly coat, expressive eyes, premium urban companion",
        "hashtags": ["#ToyPoodle", "#PoodleMY", "#DogWellness", "#DogParents"],
    },
    {
        "key": "pomeranian",
        "label": "Pomeranian",
        "category": "dog",
        "scene_name": "pomeranian",
        "traits": "small fluffy pomeranian, fox-like face, lively premium apartment pet",
        "hashtags": ["#Pomeranian", "#PomMY", "#DogWellness", "#DogParents"],
    },
    {
        "key": "shih-tzu",
        "label": "Shih Tzu",
        "category": "dog",
        "scene_name": "shih tzu",
        "traits": "well-groomed shih tzu, silky coat, gentle family companion, polished home-living aesthetic",
        "hashtags": ["#ShihTzu", "#ShihTzuMY", "#DogWellness", "#DogParents"],
    },
    {
        "key": "golden-retriever",
        "label": "Golden Retriever",
        "category": "dog",
        "scene_name": "golden retriever",
        "traits": "friendly golden retriever, warm golden coat, family lifestyle dog, premium outdoor energy",
        "hashtags": ["#GoldenRetriever", "#RetrieverMY", "#DogWellness", "#DogParents"],
    },
    {
        "key": "corgi",
        "label": "Corgi",
        "category": "dog",
        "scene_name": "corgi",
        "traits": "adorable corgi, short legs, happy alert expression, premium city-pet lifestyle",
        "hashtags": ["#Corgi", "#CorgiMY", "#DogWellness", "#DogParents"],
    },
]
STYLE_BANK = {
    "soft-premium": {
        "dog_voice": "calm, elevated, warm, premium, never pushy",
        "cat_voice": "gentle, polished, reassuring, premium, never loud",
    },
    "conversion-premium": {
        "dog_voice": "premium but conversion-aware, clearer problem-to-solution flow, still soft-sell",
        "cat_voice": "premium but conversion-aware, gentle but more purposeful, still calm",
    },
    "manglish-lite": {
        "dog_voice": "premium Malaysian tone with light natural Manglish, polished but relatable",
        "cat_voice": "premium Malaysian tone with light natural Manglish, gentle and relatable",
    },
    "chinese-my-lite": {
        "dog_voice": "premium Malaysia Chinese tone with light Chinese-MY phrasing, still clean and branded",
        "cat_voice": "premium Malaysia Chinese tone with light Chinese-MY phrasing, calm and premium",
    },
}

PRODUCT_ANGLE_BANK = {
    1: {
        "key": "daily-wellness",
        "focus": ["daily wellness", "vitality", "steady energy", "routine consistency"],
        "dog_problem": "keeping energy, appetite, and daily rhythm looking stable",
        "product_reason": "supports a cleaner and more consistent everyday wellness routine",
    },
    2: {
        "key": "joint-comfort",
        "focus": ["joint comfort", "mobility", "stairs", "slippery tiles", "aging dogs"],
        "dog_problem": "movement comfort during walks, stairs, tiled floors, and aging moments",
        "product_reason": "supports a more comfortable and easier-moving daily routine",
    },
    3: {
        "key": "digestive-gentle-care",
        "focus": ["digestion", "hydration", "low lactose", "picky habits", "sensitive stomach"],
        "cat_problem": "building a gentler routine for digestion, hydration, and picky indoor-cat habits",
        "product_reason": "fits a softer digestion-support rhythm that feels easier to maintain",
    },
}


CTA_BANK = {
    1: {
        "save": [
            'Save this for your next pawrent routine reset.',
            'Keep this as a reference for a softer daily wellness routine.',
        ],
        "dm": [
            'DM us "wellness" if you want a softer daily routine idea.',
            'DM us "routine" if you want a cleaner wellness setup for your furkid.',
        ],
        "share": [
            'Send this to a pawrent friend building a better daily routine.',
            'Share this with someone who loves calm, premium pet care.',
        ],
        "comment": [
            'Comment "routine" if this feels like your kind of pawrent life.',
            'Comment "daily" if you want more content like this.',
        ],
    },
    2: {
        "save": [
            'Save this if your dog is slowing down on walks or stairs.',
            'Keep this for the season when movement comfort starts to matter more.',
        ],
        "dm": [
            'DM us "joint" if your furkid needs a more comfortable daily rhythm.',
            'DM us "mobility" if you want a softer joint-support routine.',
        ],
        "share": [
            'Send this to a pawrent friend with a senior or active dog at home.',
            'Share this with someone whose dog is starting to move a little slower.',
        ],
        "comment": [
            'Comment "comfort" if your dog loves daily walks too.',
            'Comment "joint" if this sounds like your current concern.',
        ],
    },
    3: {
        "save": [
            'Save this for the next time your cat feels picky or off routine.',
            'Keep this if your cat does best with a gentler daily rhythm.',
        ],
        "dm": [
            'DM us "digest" if your cat does better with a gentler routine.',
            'DM us "cat" if you want a softer digestion-support routine idea.',
        ],
        "share": [
            'Send this to a cat parent who is trying to build a calmer feeding routine.',
            'Share this with someone caring for a picky indoor cat.',
        ],
        "comment": [
            'Comment "gentle" if your cat prefers a softer routine too.',
            'Comment "cat" if you want more premium cat-care content.',
        ],
    },
}


THEME_TAGS = {
    'kl-morning-routine': ['#KLMorning', '#MorningRoutine', '#UrbanPawrents'],
    'park-lifestyle': ['#ParkLifestyle', '#WeekendWalks', '#PremiumPawrents'],
    'senior-comfort-kl': ['#SeniorPetCare', '#ComfortRoutine', '#GentleSupport'],
    'terrace-home-living': ['#TerraceHouseLife', '#HomePetRoutine', '#ModernPawrents'],
    'rainy-day-indoor': ['#RainyDayRoutine', '#IndoorPetLife', '#CalmPetCare'],
    'weekend-park-walk': ['#WeekendPawrents', '#ParkWalkRoutine', '#OutdoorPetLife'],
    'city-pawrent-rhythm': ['#CityPawrents', '#UrbanPetRoutine', '#BusyButBalanced'],
}

PRODUCT_TAGS = {
    1: ['#DailyWellness', '#DailyVitality', '#EverydayPetSupport'],
    2: ['#JointSupport', '#MobilityCare', '#ActiveAgingPets'],
    3: ['#DigestiveCare', '#GentleTummies', '#HydrationRoutine'],
}

CAT_TYPES = [
    {
        "key": "british-shorthair",
        "label": "British Shorthair",
        "category": "cat",
        "scene_name": "british shorthair cat",
        "traits": "plush british shorthair cat, round face, calm premium indoor companion",
        "hashtags": ["#BritishShorthair", "#CatWellness", "#CatParents", "#CatsofMalaysia"],
    },
    {
        "key": "ragdoll",
        "label": "Ragdoll",
        "category": "cat",
        "scene_name": "ragdoll cat",
        "traits": "beautiful ragdoll cat, soft long coat, blue eyes, elegant premium home presence",
        "hashtags": ["#Ragdoll", "#CatWellness", "#CatParents", "#CatsofMalaysia"],
    },
    {
        "key": "persian",
        "label": "Persian",
        "category": "cat",
        "scene_name": "persian cat",
        "traits": "luxurious persian cat, fluffy coat, calm regal look, premium indoor pet aesthetic",
        "hashtags": ["#PersianCat", "#CatWellness", "#CatParents", "#CatsofMalaysia"],
    },
    {
        "key": "scottish-fold",
        "label": "Scottish Fold",
        "category": "cat",
        "scene_name": "scottish fold cat",
        "traits": "cute scottish fold cat, folded ears, round expressive face, polished indoor lifestyle",
        "hashtags": ["#ScottishFold", "#CatWellness", "#CatParents", "#CatsofMalaysia"],
    },
    {
        "key": "domestic-short-hair",
        "label": "Domestic Short Hair",
        "category": "cat",
        "scene_name": "domestic short hair cat",
        "traits": "healthy domestic short hair cat, sleek coat, relaxed home companion, natural Malaysian household feel",
        "hashtags": ["#DomesticShortHair", "#CatWellness", "#CatParents", "#CatsofMalaysia"],
    },
]


def read_state() -> int:
    if not STATE_FILE.exists():
        return 1
    try:
        raw = STATE_FILE.read_text(encoding="utf-8").strip()
        value = int(raw)
        if value in (1, 2, 3):
            return value
    except Exception:
        pass
    return 1


def next_product(current: int) -> int:
    return {1: 2, 2: 3, 3: 1}.get(current, 1)


def write_state(value: int) -> None:
    STATE_FILE.write_text(str(value), encoding="utf-8")


def product_info(product_id: int) -> tuple[str, str | None]:
    mapping = {
        1: ("Glumoo Daily Wellness Formula", str(REF_DIR / "sku1.png")),
        2: ("Glumoo JointCare Goat Milk Powder", str(REF_DIR / "sku2.jpg")),
        3: ("Glumoo Digestive Care Goat Milk Powder", str(REF_DIR / "sku3.jpg")),
    }
    return mapping.get(product_id, mapping[1])


def theme_for_date(date_str: str) -> dict:
    day = int(date_str[-2:])
    return THEMES[(day - 1) % len(THEMES)]


def pet_profile_for_date(date_str: str, product_id: int) -> dict:
    day = int(date_str[-2:])
    if product_id == 3:
        pool = CAT_TYPES
    else:
        pool = DOG_TYPES
    return pool[(day - 1) % len(pool)]


def style_for_date(date_str: str) -> tuple[str, dict]:
    styles = ["soft-premium", "conversion-premium", "manglish-lite", "chinese-my-lite"]
    style_key = styles[(int(date_str[-2:]) - 1) % len(styles)]
    return style_key, STYLE_BANK[style_key]


def cta_for_date(date_str: str, product_id: int) -> str:
    day = int(date_str[-2:])
    bank = CTA_BANK.get(product_id, CTA_BANK[1])
    kinds = ["save", "dm", "share", "comment"]
    kind = kinds[(day - 1) % len(kinds)]
    pool = bank[kind]
    return pool[(day - 1) % len(pool)]


def dynamic_hashtags(theme_key: str, product_id: int, pet: dict) -> list[str]:
    tags = []
    tags.extend(pet.get('hashtags', []))
    tags.extend(PRODUCT_TAGS.get(product_id, []))
    tags.extend(THEME_TAGS.get(theme_key, []))
    seen = set()
    out = []
    for tag in BASE_HASHTAGS + tags:
        if tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out[:15]


def storyboard_prompts(theme: dict, product_id: int, product_name: str, ref_image: str | None, pet: dict, date_str: str) -> list[str]:
    day = int(date_str[-2:])
    subject = pet["scene_name"]
    traits = pet["traits"]
    overlay_lines = premium_overlay_lines(product_id, pet["category"])
    routine_phrase = "feeding or care ritual" if pet["category"] == "dog" else "feeding, hydration, or care ritual"

    human_pool = [
        "young Malaysian Chinese woman in elevated casual homewear",
        "modern Malaysian couple in polished weekend attire",
        "stylish urban pawrent in clean neutral tones",
        "refined Malaysian family member in relaxed luxury homewear",
        "confident Malaysian professional in off-duty premium casualwear",
        "warm family-style pawrent in understated luxury basics",
    ]
    camera_pool = [
        "editorial wide shot",
        "natural eye-level lifestyle shot",
        "slightly cinematic medium shot",
        "close candid premium lifestyle frame",
        "elevated three-quarter composition",
        "soft documentary-style composition",
    ]
    lighting_pool = [
        "soft tropical morning light",
        "clean bright daylight",
        "golden late-afternoon light",
        "soft overcast luxury daylight",
        "window-lit indoor daylight",
        "post-rain diffused daylight",
    ]
    scene_twists = [
        "include refined Malaysian residential details and tropical landscaping cues",
        "show a believable Kuala Lumpur premium-home atmosphere, not generic western suburb styling",
        "ground the image in Malaysian urban living with polished but realistic architecture",
        "keep the environment premium, local, and naturally lived-in rather than staged",
        "make the setting feel recognisably Malaysian through layout, greenery, materials, and daily-life details",
        "avoid generic stock-photo staging and build a more believable lived-in premium home rhythm",
    ]

    theme_banks = {
        "senior-comfort-kl": {
            "departure": [
                "pet stepping carefully across a tiled condo walkway with soft morning pace",
                "pet standing calmly beside the pawrent near a lift lobby or sheltered drop-off, easy movement and no rush",
                "pet moving gently along a shaded residential path with a slower, comfort-first stride",
                "pet pausing before a short walk near the home entry with quiet low-energy body language",
            ],
            "lifestyle": [
                "pet resting beside a sofa or lounge chair while the pawrent keeps watch nearby, product integrated clearly on a side table",
                "pet relaxing near a shoe bench or entry console after coming home, product pack shown clearly and elegantly",
                "pet settled beside the pawrent in a calm indoor recovery scene, product clearly visible on a coffee table",
                "pet resting by cool flooring and daylight, product placed front-facing on a low cabinet or side surface",
            ],
            "bond": [
                "quiet reassurance moment with the pawrent seated nearby, attention on the pet's comfort and ease",
                "easy pause on a rug or cool tile with the pawrent offering calm presence rather than performance",
                "soft companionship scene near a window corner, the pet settled and emotionally secure",
                "slow affectionate moment near the home entrance after a short outing, premium lived-in realism",
            ],
            "care": [
                "hydration corner moment with a water bowl, tidy floor zone, and quiet premium home rhythm",
                "post-walk paw-wipe or towel-care moment transitioning naturally into the daily routine setup",
                "home routine scene with the pet waiting calmly near a bowl or water station while the pawrent prepares the next step",
                "easy kitchen, pantry, or feeding-corner setup that feels realistic for an older dog's slower daily rhythm",
                "settling-back-in moment near an entry console or shoe bench after care is done, premium lived-in calm",
                "quiet supplement-prep or home-care setup where the ritual is implied rather than dramatic feeding action",
            ],
        },
        "weekend-park-walk": {
            "departure": [
                "pet waiting at the door while the pawrent prepares the leash for a calm weekend outing",
                "pet standing alert near a shaded jogging path while the pawrent adjusts the leash",
                "pet waiting at a crosswalk or path junction before heading into a park, city-weekend rhythm",
                "pet stepping out from a condo forecourt into a landscaped morning community scene",
            ],
            "lifestyle": [
                "pet enjoying an open green stretch during a calm weekend walk with relaxed happy stride",
                "pet moving through a landscaped premium neighborhood park with confident weekend energy",
                "pet trotting beside the pawrent near a lake edge or open lawn in a polished community park",
                "pet exploring a tropical landscaped corner with breezy weekend freedom and premium park atmosphere",
            ],
            "bond": [
                "mid-walk bonding pause with natural interaction and community greenery around them",
                "quiet shoulder-to-shoulder pause near a park rail or landscaped curb, premium city-lifestyle energy",
                "rest moment after light exercise with genuine human-pet connection rather than posed affection",
                "calm pause on a shaded path while the pawrent smiles and the pet resets comfortably",
            ],
            "care": [
                "pet near the home's entry corner with leash, towel, and product arranged as a polished return-home scene",
                "after-walk hydration and care setup with water bowl, towel, and easy home rhythm",
                "entryway-to-kitchen routine transition with the pet waiting naturally for the next step",
                "smart post-park routine scene with product and neat daily-care styling, not necessarily active feeding",
                "cool-down moment near a shoe bench, towel basket, or water station after outdoor time",
                "post-walk settle-in scene where the routine feels complete without needing a pouring action",
            ],
        },
        "rainy-day-indoor": {
            "departure": [
                "pet near a large rain-lit window with tropical rain ambience outside and quiet indoor mood",
                "pet watching the rainy balcony or patio edge from inside a premium KL apartment",
                "pet settled near sliding doors with wet greenery visible outside and calm indoor softness",
                "pet looking out toward a rainy terrace while staying dry in a serene premium home setting",
            ],
            "lifestyle": [
                "pet relaxing beside the pawrent in a bright indoor corner, product clearly visible on a side table or cabinet",
                "pet curled near a sofa or lounge chair while the product pack sits front-facing nearby",
                "pet in a calm window-side resting scene with product placed clearly on a console or sideboard",
                "pet sharing a quiet indoor afternoon with the pawrent while the product remains obviously present in frame",
            ],
            "bond": [
                "soft trust moment on rug or cool flooring while tropical rain ambience stays outside the window",
                "quiet companionship scene with a blanket, rug, or low seating area and understated affection",
                "stillness-heavy bonding moment where the room feels calm, clean, and emotionally safe",
                "pet and pawrent sharing a low-energy rainy-day pause with premium but lived-in realism",
            ],
            "care": [
                "rainy-day home routine with product and simple comforts arranged beautifully",
                "quiet kitchen or pantry care moment with the pet waiting nearby while the routine unfolds",
                "warm indoor hydration setup or light feeding ritual suited to a slower weather-softened day",
                "gentle apartment ritual that feels appropriate for staying in during tropical rain",
                "window-side settle-in routine with towel, mat, or water station details",
                "soft indoor care scene where comfort matters more than an obvious serving gesture",
            ],
        },
        "terrace-home-living": {
            "departure": [
                "pet stepping through a modern terrace house entryway or front-lawn transition with polished everyday energy",
                "pet near the gate, porch, or car porch area of a premium terrace home, relaxed daily rhythm",
                "pet moving between indoor and outdoor threshold spaces in a believable family-home setting",
                "pet walking across a neat front approach path with relaxed residential confidence",
            ],
            "lifestyle": [
                "pet in a styled living or dining area, product placed naturally and clearly within a real family home scene",
                "pet beside a dining bench or living-room console with the product pack clearly visible",
                "pet near a kitchen island or side cabinet with product integrated into believable domestic life",
                "pet settled in a bright common area with the product displayed naturally but obviously",
            ],
            "bond": [
                "easy bonding pause in a terrace-home corridor, porch, or family common space",
                "gentle pause near a staircase, hallway, or lounge corner with understated affection",
                "pet and pawrent sharing a soft domestic moment near the day's in-between spaces",
                "warm, low-drama companionship inside a premium but practical Malaysian family home",
            ],
            "care": [
                "daily care setup in a clean kitchen or feeding corner with premium but repeatable action",
                "home routine scene near pantry shelving, a kitchen nook, or a low counter care zone",
                "easy care sequence near the dining area or utility corner, tidy and realistic",
                "calm kitchen-side routine that feels like part of a household's normal rhythm",
                "terrace-home settle-in moment with a mat, water bowl, towel, or quiet post-walk detail",
                "domestic routine image where the product supports the ritual without forcing a feeding-pour scene",
            ],
        },
        "kl-morning-routine": {
            "departure": [
                "pet waiting by the door for the first short walk of the morning in a polished KL home",
                "pet stepping into the day near a condo corridor, lift lobby, or landscaped drop-off with fresh-start energy",
                "pet stretching near a bright balcony threshold before the city gets busy",
                "pet moving through cool morning light across a condo common area or balcony edge",
            ],
            "lifestyle": [
                "pet inside a sunlit breakfast or living area, product integrated elegantly and clearly into the morning scene",
                "pet near a breakfast counter or coffee table while the product pack sits visible and front-facing",
                "pet in a condo living area with the product integrated into a believable first-hour routine",
                "pet near cool morning flooring and soft daylight while the product remains clearly visible nearby",
            ],
            "bond": [
                "slow morning bonding moment with the pawrent before the day gets busy",
                "quiet just-after-waking companionship scene with the city still soft outside",
                "gentle morning reset moment near a window, sofa, or breakfast nook",
                "pet leaning into a calm first-ritual pause before the pace of the day begins",
            ],
            "care": [
                "clean morning ritual with daylight across counters or flooring and an easy care rhythm",
                "breakfast-hour care sequence in a bright condo corner with polished realism",
                "morning hydration or light feeding ritual that feels tidy, premium, and genuinely repeatable",
                "simple polished morning-care action suited to a KL condo lifestyle",
                "first-routine-of-the-day scene near a water station, bowl, or entry bench",
                "gentle morning prep moment where the routine is clear without forcing a pouring action",
            ],
        },
        "park-lifestyle": {
            "departure": [
                "pet pausing on a premium community lawn with elegant easy-going outdoor rhythm",
                "pet near a shaded park bridge, path curve, or garden bend in a believable lifestyle moment",
                "pet beside the pawrent at a green residential corner with breezy premium atmosphere",
                "pet in a leafy outdoor lifestyle scene that feels local, upscale, and naturally active",
            ],
            "lifestyle": [
                "pet walking through a landscaped premium neighborhood park with polished lifestyle energy",
                "pet moving through tropical greenery near a residential jogging path or pond edge",
                "pet in a return-home park-lifestyle scene with the product pack clearly visible near the entry or bench",
                "pet beside a balcony or lounge area after the walk, product integrated clearly and tastefully",
            ],
            "bond": [
                "easy outdoor trust moment under tropical greenery with believable premium community feeling",
                "pet and pawrent sharing a relaxed bonding pause after walking through landscaped paths",
                "natural companionship scene in green space that feels lived-in and local rather than stock-like",
                "gentle connection moment with fresh-air calm and premium neighborhood atmosphere",
            ],
            "care": [
                "post-outdoor care ritual back home with a premium but natural recovery setup",
                "easy transition from walk to hydration or light feeding in a realistic premium-home care corner",
                "care sequence with product and park-life return energy still visible in the styling",
                "gentle after-park routine with polished countertop, water station, or feeding-zone detail",
                "after-park settle-in moment with towel, mat, leash, or water bowl as believable routine objects",
                "recovery-style home ritual where the dog is winding down rather than always actively eating",
            ],
        },
        "city-pawrent-rhythm": {
            "departure": [
                "pet walking near a condo forecourt, sheltered driveway, or landscaped city entrance",
                "pet pausing by a lift lobby, corridor threshold, or minimalist urban walkway",
                "pet moving through a polished urban residential setting with efficient city-life rhythm",
                "pet in a sleek city-home threshold scene that feels modern Malaysian rather than generic western",
            ],
            "lifestyle": [
                "pet in a modern compact luxury home scene, product clearly integrated into a realistic city routine",
                "pet near a compact condo console, sideboard, or breakfast ledge with product visible and obvious",
                "pet beside the pawrent in a compact premium interior where product placement feels believable",
                "pet in a stylish KL condo corner with the product pack clearly anchored in the scene",
            ],
            "bond": [
                "brief calm pause between urban moments with stylish pawrent energy and believable KL context",
                "pet and pawrent sharing a quiet reset inside a compact premium home",
                "soft low-drama companionship in a city apartment that still feels warm and human",
                "subtle bonding scene where city rhythm slows down briefly for the pet's comfort",
            ],
            "care": [
                "smart practical daily routine setup in a compact premium kitchen or care zone",
                "city-home care ritual with product and clean efficient spatial styling",
                "pet waiting by a compact bowl or water station while the pawrent completes a neat routine",
                "well-designed compact-home routine that still feels calm and caring rather than rushed",
                "urban settle-in scene at the entry, console, or kitchen nook after the outside world",
                "compact-home ritual where care is implied through setup and body language, not always a serving motion",
            ],
        },
    }

    fallback_bank = {
        "departure": [
            "pet moving through a believable premium residential threshold scene with daily-life realism",
            "pet waiting calmly near a door, walkway, or home transition point",
            "pet in an elegant local lifestyle setup that feels naturally lived-in",
            "pet stepping into a calm premium day with Malaysian residential context",
        ],
        "lifestyle": [
            "pet beside the pawrent in a bright premium home scene with the product clearly visible",
            "pet resting near a sofa or console while the product pack sits front-facing in frame",
            "pet in a believable lifestyle room where the product is obvious but naturally integrated",
            "pet near a side table or cabinet with the product clearly visible at first glance",
        ],
        "bond": [
            "quiet bonding moment with gentle hand contact and relaxed emotional warmth",
            "soft trust-heavy moment that feels lived-in rather than staged",
            "pet and pawrent sharing a calm reassurance scene with understated affection",
            "easy companionship pause in a clean bright premium home environment",
        ],
        "care": [
            "daily home-care setup with product, bowl, and realistic feeding-corner detail",
            "pet waiting calmly during a polished but believable routine sequence",
            "feeding or care scene that feels premium yet repeatable in normal life",
            "close routine moment with bowl, scoop, and the pet focused on the care ritual",
        ],
    }

    narrative_orders = {
        "senior-comfort-kl": [
            ["departure", "bond", "lifestyle", "care"],
            ["departure", "lifestyle", "bond", "care"],
            ["lifestyle", "departure", "bond", "care"],
        ],
        "weekend-park-walk": [
            ["departure", "lifestyle", "bond", "care"],
            ["lifestyle", "bond", "departure", "care"],
            ["departure", "bond", "care", "lifestyle"],
        ],
        "rainy-day-indoor": [
            ["departure", "lifestyle", "bond", "care"],
            ["lifestyle", "bond", "departure", "care"],
            ["bond", "departure", "lifestyle", "care"],
        ],
        "terrace-home-living": [
            ["departure", "lifestyle", "bond", "care"],
            ["lifestyle", "departure", "bond", "care"],
            ["departure", "bond", "lifestyle", "care"],
        ],
        "kl-morning-routine": [
            ["departure", "bond", "lifestyle", "care"],
            ["departure", "lifestyle", "care", "bond"],
            ["lifestyle", "departure", "bond", "care"],
        ],
        "park-lifestyle": [
            ["departure", "lifestyle", "bond", "care"],
            ["lifestyle", "departure", "bond", "care"],
            ["bond", "lifestyle", "departure", "care"],
        ],
        "city-pawrent-rhythm": [
            ["departure", "lifestyle", "bond", "care"],
            ["lifestyle", "bond", "departure", "care"],
            ["departure", "care", "lifestyle", "bond"],
        ],
    }

    kind_specs = {
        "departure": {
            "base": "Premium lifestyle departure image",
            "product_required": False,
            "mood": "opening scene and daily rhythm",
        },
        "lifestyle": {
            "base": "Premium product lifestyle image",
            "product_required": True,
            "mood": "branded lived-in lifestyle credibility",
        },
        "bond": {
            "base": "Premium emotional trust image",
            "product_required": False,
            "mood": "quiet connection and premium warmth",
        },
        "care": {
            "base": "Premium routine care image",
            "product_required": True,
            "mood": "daily care realism",
        },
    }

    bank = theme_banks.get(theme["key"], fallback_bank)
    order_pool = narrative_orders.get(theme["key"], [["departure", "lifestyle", "bond", "care"]])
    narrative_order = order_pool[(day - 1) % len(order_pool)]

    def choose(pool: list[str], offset: int) -> str:
        return pool[(day - 1 + offset) % len(pool)]

    anti_repeat_rules = [
        "across the full 4-image set, avoid repeating the same action pattern in multiple slides",
        "do not make multiple slides feel like the same walk, the same crouch-and-pet pose, or the same bowl-serving gesture",
        "each slide should introduce a clearly distinct scene function, body posture, and moment in the day",
        "vary human posture across the set: not all standing, not all crouching, not all touching the pet in the same way",
        "if one slide is outdoor walking, the others should pivot into different actions rather than restaging the same movement",
    ]

    prompts = []
    used_kind_signals = []
    for idx, kind in enumerate(narrative_order):
        spec = kind_specs[kind]
        frame = choose(bank.get(kind, fallback_bank[kind]), idx)
        camera = camera_pool[(day + idx + 1) % len(camera_pool)]
        lighting = lighting_pool[(day + idx + 2) % len(lighting_pool)]
        human = human_pool[(day + idx) % len(human_pool)]
        twist = choose(scene_twists, idx)
        overlay = overlay_lines[idx % len(overlay_lines)]

        product_rule = ""
        if spec["product_required"]:
            product_rule = (
                " the Glumoo product pack must be clearly visible, front-facing, unobstructed, large enough to be noticed immediately, "
                "readable at a glance, and accurately match the reference image; do not omit the product; this image fails if the pack is tiny, hidden, turned away, or missing."
            )

        routine_detail = ""
        if kind == "care":
            routine_detail = (
                f" feature {subject} during a {routine_phrase}; bowls, scoop, towel, leash, water bowl, mat, entry bench, or adjacent routine objects can appear only when they fit naturally; avoid defaulting to a spoon-pouring-into-bowl action unless the specific scene genuinely calls for it."
            )

        diversity_detail = ""
        prior = ", ".join(used_kind_signals)
        if prior:
            diversity_detail = f" avoid repeating prior scene functions already used in this set: {prior}. "
        diversity_detail += anti_repeat_rules[idx % len(anti_repeat_rules)] + "."

        prompt = (
            f"{spec['base']}, 4:5, {camera}, {lighting}, {human} with {subject}, {frame}, "
            f"set in {theme['scene']}, {traits}, mood: {spec['mood']}, {twist},{product_rule}{routine_detail} {diversity_detail} "
            f"premium headline text printed directly on the image saying: '{overlay}', no white text box, no big white background block, no label card, "
            "use larger elegant typography that is clearly readable at a glance, integrate the text naturally into the image composition, no watermark."
        )
        if spec["product_required"] and ref_image:
            prompt += f" Reference: {ref_image}"
        prompts.append(prompt)
        used_kind_signals.append(kind)
    return prompts

def build_plan(product_id: int, date_str: str) -> DailyPlan:
    product_name, ref_image = product_info(product_id)
    theme = theme_for_date(date_str)
    pet = pet_profile_for_date(date_str, product_id)
    cta = cta_for_date(date_str, product_id)
    style_key, _style = style_for_date(date_str)
    day = int(date_str[-2:])

    if pet["category"] == "dog":
        if product_id == 1:
            hooks = [
                "The best dog routines do not need to feel loud to feel beautiful.",
                "Sometimes good pet care simply looks like a home that runs softly and a dog that feels well.",
                "Premium dog wellness usually lives in the quiet details of the day.",
            ]
            scene_options = [
                "Morning light through a KL condo window. A clean bowl. Cool floors. An easy start before the city gets busy.",
                "In polished Malaysian homes, the nicest routines often feel almost invisible - just good light, a steady pace, and care that sits naturally inside the day.",
                "Between landscaped residences, tidy interiors, and evening walks downstairs, daily care should feel easy to return to.",
            ]
            issue_options = [
                f"The real luxury is often consistency - a {pet['label']} that stays bright, settled, and comfortable in the rhythm of everyday life.",
                f"With a {pet['label']}, wellness often shows up in small signs first: easy appetite, steady energy, a body that feels quietly well supported.",
                f"What most pawrents want is simple - a {pet['label']} that feels well, without the routine feeling heavy around it.",
            ]
            product_options = [
                f"That is where {product_name} slips in naturally - soft support, worked quietly into the routine.",
                f"{product_name} belongs in this kind of home because it adds care without adding noise.",
                f"In a routine like this, {product_name} feels less like a push and more like a detail that simply fits.",
            ]
        else:
            hooks = [
                "Sometimes the first sign of age is simply less ease.",
                "You notice it in the small things first.",
                "When movement changes, comfort becomes part of good care.",
            ]
            scene_options = [
                "A slower walk under rain trees. Tiled floors at home. A routine designed to feel softer on the body.",
                "In KL homes and private residences, movement comfort often becomes part of premium care long before it becomes a big conversation.",
                "The thoughtful version of dog care notices the little things first - stairs, smooth floors, the way a dog settles after rest.",
            ]
            issue_options = [
                f"For many {pet['label']}s, comfort begins to matter most in the ordinary moments - getting up, taking stairs, finding ease again after rest.",
                f"With a {pet['label']}, mobility is rarely one dramatic issue. It is usually a softer change in the way the day is carried.",
                f"The goal is rarely speed. It is ease, confidence, and a routine that asks a little less from the body.",
            ]
            product_options = [
                f"That is why {product_name} works here - folded into the day, adding comfort without changing the tone of the home.",
                f"{product_name} fits this kind of premium rhythm because the care feels gentle, not clinical.",
                f"In a softer routine, {product_name} supports comfort in a way that still feels calm and beautifully livable.",
            ]

        hook = hooks[day % len(hooks)]
        scene_line = scene_options[day % len(scene_options)]
        issue_line = issue_options[day % len(issue_options)]
        product_line = product_options[day % len(product_options)]

        if style_key == "manglish-lite":
            hook += " Very natural, very ngam for daily life lah."
        elif style_key == "chinese-my-lite":
            hook += ""

    else:
        hooks = [
            "Some forms of care are meant to be felt, not announced.",
            "A softer routine changes more than we think.",
            "The gentlest parts of the day often matter most.",
        ]
        scene_options = [
            "Filtered light across a KL apartment. Cool floors. A quiet window corner. A feeding routine that barely disturbs the room.",
            "In polished Malaysian homes, the nicest cat routines often feel almost invisible - a clean bowl, soft pacing, and an atmosphere the cat never has to fight against.",
            "For indoor cats, premium care often begins with atmosphere: daylight, quiet spaces, and rituals that feel easy on the body.",
        ]
        issue_options = [
            f"With many {pet['label']}s, the shift is subtle at first - a little more hesitation, a little more fussiness, a routine that no longer feels quite as smooth.",
            f"Sensitive digestion and picky habits rarely arrive as one loud problem. They usually settle quietly into the texture of the day.",
            f"For many cat parents, the real goal is not perfection - just a routine that feels gentler, easier, and calmer to live with.",
        ]
        product_options = [
            f"That is where {product_name} belongs - sitting gently inside the routine, adding support without changing its softness.",
            f"{product_name} makes sense here because it keeps the whole rhythm feeling calmer, easier, and more settled.",
            f"In a home like this, {product_name} feels less like intervention and more like part of the atmosphere.",
        ]

        hook = hooks[day % len(hooks)]
        scene_line = scene_options[day % len(scene_options)]
        issue_line = issue_options[day % len(issue_options)]
        product_line = product_options[day % len(product_options)]

        if style_key == "manglish-lite":
            hook += " Once the routine a bit off, the whole home also feels it."
        elif style_key == "chinese-my-lite":
            hook += " 猫咪舒服，整个家的节奏都会柔下来。"

    cta_map = {
        "Save this for the next time your cat feels picky or off routine.": "Keep this one close.",
        'DM "digest" if your cat has been feeling picky lately.': 'If your cat has been a little picky lately, DM us "digest".',
        "Share this with a cat parent who is trying to improve the daily routine.": "Send this to someone building a softer routine at home.",
        "Comment if your cat has ever gone through a picky phase.": "If this sounds familiar, you are probably not the only one.",
        "Save this for the next time your dog feels stiff after rest.": "Keep this close for the slower days.",
        'DM "joint" if your dog has been slowing down lately.': 'If your dog has been moving a little differently lately, DM us "joint".',
        "Share this with a pawrent whose dog is getting older.": "Send this to someone learning how to care for an older dog well.",
        "Comment if your dog has started taking stairs more slowly.": "If you have been noticing the small changes too, you are not imagining it.",
        "Save this as a gentle reminder that consistent care matters.": "A soft reminder: the routines we keep often matter most.",
        "DM us if you want help choosing the right Glumoo routine.": "If you want help choosing the right Glumoo routine, we are here.",
        "Share this with a fellow pawrent building a better routine.": "Send this to a fellow pawrent who would appreciate a softer routine.",
        "Comment if your pet thrives on a steady daily routine.": "Some pets really do flourish when the routine feels right.",
    }
    final_cta = cta_map.get(cta, cta)

    caption = "\n\n".join([
        hook,
        scene_line,
        issue_line,
        product_line,
        final_cta,
    ])

    prompts = storyboard_prompts(theme, product_id, product_name, ref_image, pet, date_str)
    hashtags = dynamic_hashtags(theme["key"], product_id, pet)
    return DailyPlan(
        product_id=product_id,
        product_name=product_name,
        ref_image=ref_image,
        theme_key=theme["key"],
        theme_label=theme["label"],
        caption=caption,
        hashtags=hashtags,
        image_prompts=prompts,
    )


def premium_overlay_lines(product_id: int, pet_category: str) -> list[str]:
    if pet_category == "cat":
        if product_id == 3:
            return [
                "Gentle care, beautifully kept",
                "Soft routines matter",
                "Comfort in the quiet details",
                "Made for calmer days",
            ]
        return [
            "Quiet care, every day",
            "Softness in the routine",
            "A calmer kind of care",
            "Beautifully easy support",
        ]
    if product_id == 2:
        return [
            "Comfort, kept close",
            "For gentler movement",
            "Support in the small moments",
            "Made for easier days",
        ]
    return [
        "Quiet care, every day",
        "Wellness in the details",
        "Soft routines, better days",
        "Made to fit the everyday",
    ]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_caption(path: Path, plan: DailyPlan) -> None:
    content = plan.caption + "\n\nHashtags\n" + " ".join(plan.hashtags) + "\n"
    path.write_text(content, encoding="utf-8")


def run_cmd(cmd: list[str], retries: int = 1, delay: float = 2.0, env: dict[str, str] | None = None) -> None:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            subprocess.run(cmd, check=True, env=env)
            return
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay * (attempt + 1))
                continue
            raise
    if last_error:
        raise last_error


def _build_image_generate_url(base_url: str, model_id: str) -> str:
    base = base_url.rstrip("/")
    if "generativelanguage.googleapis.com" in base:
        normalized = model_id if model_id.startswith("models/") else f"models/{model_id}"
        return f"{base}/v1beta/{normalized}:generateContent"
    normalized = model_id.replace("models/", "", 1)
    return f"{base}/v1beta/models/{normalized}:generateContent"


def _generate_image_via_api(prompt: str, output: Path, input_images: list[str], api_key: str, base_url: str, model_id: str) -> None:
    parts: list[dict] = []
    for img in input_images:
        img_path = Path(img)
        if not img_path.exists():
            continue
        mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
        parts.append({
            "inline_data": {
                "mime_type": mime,
                "data": base64.b64encode(img_path.read_bytes()).decode("ascii"),
            }
        })
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 0.8,
        },
    }

    headers = {"Content-Type": "application/json"}
    if "generativelanguage.googleapis.com" in base_url:
        headers["x-goog-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        _build_image_generate_url(base_url, model_id),
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Image API HTTP {e.code}: {body[:500]}") from e

    candidates = data.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts_out = content.get("parts") or []
        for part in parts_out:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(base64.b64decode(inline["data"]))
                return

    raise RuntimeError(f"Image API returned no image payload: {json.dumps(data)[:500]}")


def generate_images(out_dir: Path, plan: DailyPlan) -> None:
    dog_anchor: Path | None = None

    for idx, prompt in enumerate(plan.image_prompts, start=1):
        output = out_dir / f"p{idx}.png"

        anchor_note = ""
        input_images: list[str] = []

        if idx == 1:
            input_images = []
        elif dog_anchor and dog_anchor.exists():
            input_images = [str(dog_anchor)]
            anchor_note = " Use the same dog as the reference image (same breed, coat pattern, face, and vibe)."

        if idx in (2, 4) and plan.ref_image and Path(plan.ref_image).exists():
            input_images = [img for img in input_images if Path(img).exists()]
            input_images.append(plan.ref_image)
            prompt = (
                prompt
                + " The Glumoo package must be clearly visible in the frame, front-facing, unobstructed, and easy to notice immediately."
                + " The image is not acceptable if the product pack is missing, too tiny, turned away, or hidden."
                + " Ensure the product packaging matches the reference image exactly."
            )

        full_prompt = prompt + anchor_note

        if XHS_IMAGE_API_KEY and XHS_IMAGE_BASE_URL:
            last_error = None
            for attempt in range(1, 3):
                try:
                    _generate_image_via_api(
                        full_prompt,
                        output,
                        input_images,
                        XHS_IMAGE_API_KEY,
                        XHS_IMAGE_BASE_URL,
                        XHS_IMAGE_MODEL,
                    )
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(2 * attempt)
                        continue
            if last_error:
                raise last_error
        else:
            cmd = [
                "uv",
                "run",
                str(NANO_BANANA),
                "--prompt",
                full_prompt,
                "--filename",
                str(output),
                "--resolution",
                "1K",
            ]

            for img in input_images:
                if img and Path(img).exists():
                    cmd.extend(["-i", img])

            image_env = os.environ.copy()
            image_env.pop("GOOGLE_API_KEY", None)

            if XHS_IMAGE_API_KEY:
                image_env["XHS_IMAGE_API_KEY"] =REDACTED_FOR_GITHUB
                image_env["GEMINI_API_KEY"] =REDACTED_FOR_GITHUB
                cmd.extend(["--api-key", XHS_IMAGE_API_KEY])
            if XHS_IMAGE_BASE_URL:
                image_env["XHS_IMAGE_BASE_URL"] = XHS_IMAGE_BASE_URL
                image_env["GEMINI_BASE_URL"] = XHS_IMAGE_BASE_URL
            if XHS_IMAGE_MODEL:
                image_env["XHS_IMAGE_MODEL"] = XHS_IMAGE_MODEL
                image_env["GEMINI_IMAGE_MODEL"] = XHS_IMAGE_MODEL

            run_cmd(cmd, retries=1, env=image_env)

        if idx == 1:
            dog_anchor = output


def mirror_output(src: Path, dst: Path) -> None:
    ensure_dir(dst)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_file():
            shutil.copy2(item, target)


def write_meta(path: Path, date_str: str, plan: DailyPlan) -> None:
    payload = {
        "date": date_str,
        "product_id": plan.product_id,
        "product_name": plan.product_name,
        "theme_key": plan.theme_key,
        "theme_label": plan.theme_label,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "image-post",
        "images": 4,
        "aspect_ratio": "4:5",
        "style": "pet-rotation",
        "market": "Malaysia",
        "city": "Kuala Lumpur",
        "ref_image": plan.ref_image,
        "text_provider": {
            "base_url": XHS_TEXT_BASE_URL,
            "model": XHS_TEXT_MODEL,
            "configured": bool(XHS_TEXT_API_KEY),
        },
        "image_provider": {
            "base_url": XHS_IMAGE_BASE_URL,
            "model": XHS_IMAGE_MODEL,
            "aspect_ratio": XHS_IMAGE_ASPECT_RATIO,
            "configured": bool(XHS_IMAGE_API_KEY),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def quality_check(out_dir: Path) -> list[str]:
    issues: list[str] = []
    caption_file = out_dir / "caption.md"
    meta_file = out_dir / "meta.json"
    if not caption_file.exists() or not caption_file.read_text(encoding="utf-8").strip():
        issues.append("caption.md missing or empty")
    else:
        caption_text = caption_file.read_text(encoding="utf-8").lower()
        if "sku" in caption_text:
            issues.append("caption contains forbidden word: sku")
    if not meta_file.exists():
        issues.append("meta.json missing")
    for idx in range(1, 5):
        image = out_dir / f"p{idx}.png"
        if not image.exists() or image.stat().st_size < 1024:
            issues.append(f"p{idx}.png missing or too small")
    return issues


def prepare_send_copy(out_dir: Path, date_str: str) -> Path:
    send_dir = SEND_ROOT / date_str
    ensure_dir(send_dir)
    for item in out_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, send_dir / item.name)
    return send_dir


def send_to_telegram(send_dir: Path) -> None:
    caption = (send_dir / "caption.md").read_text(encoding="utf-8")
    run_cmd([
        "openclaw",
        "message",
        "send",
        "--channel",
        "telegram",
        "--target",
        TELEGRAM_CHAT,
        "--message",
        caption,
    ], retries=1)
    for idx in range(1, 5):
        run_cmd([
            "openclaw",
            "message",
            "send",
            "--channel",
            "telegram",
            "--target",
            TELEGRAM_CHAT,
            "--media",
            str(send_dir / f"p{idx}.png"),
        ], retries=1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--advance-state", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    current = read_state()
    product_id = current
    plan = build_plan(product_id, args.date)

    out_dir = OUT_ROOT / args.date
    mirror_dir = MIRROR_ROOT / args.date / "ins"
    ensure_dir(out_dir)

    write_caption(out_dir / "caption.md", plan)
    generate_images(out_dir, plan)
    write_meta(out_dir / "meta.json", args.date, plan)
    mirror_output(out_dir, mirror_dir)

    issues = quality_check(out_dir)
    if issues:
        print(json.dumps({
            "status": "failed",
            "date": args.date,
            "product_id": product_id,
            "issues": issues,
            "output_dir": str(out_dir),
        }, ensure_ascii=False))
        return 1

    send_dir = prepare_send_copy(out_dir, args.date)

    delivery = "not_sent"
    if args.send:
        send_to_telegram(send_dir)
        delivery = "sent"

    if args.advance_state:
        write_state(next_product(product_id))

    print(json.dumps({
        "status": "ok",
        "date": args.date,
        "product_id": product_id,
        "product_name": plan.product_name,
        "theme_key": plan.theme_key,
        "theme_label": plan.theme_label,
        "delivery": delivery,
        "files": 6,
        "output_dir": str(out_dir),
        "send_dir": str(send_dir),
        "mirror_dir": str(mirror_dir),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
