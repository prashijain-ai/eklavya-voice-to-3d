"""Project Eklavya backend: Voice (Prisma) -> Scene JSON (Evon) -> Voice (Timbre).
Every Gnani call is env-configurable and falls back to a local demo path, so the app never dies on camera."""
import os, re, json, base64, logging
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("eklavya")
logging.basicConfig(level=logging.INFO)
E = os.getenv
app = FastAPI(title="Project Eklavya")

SYSTEM = """You are Eklavya, a spatial compiler. Input: current scene JSON + a Hindi/English code-mixed command.
Return ONLY JSON: {"scene": <updated scene>, "reply": "<short friendly Hinglish reply/clarifying question>"}.
Scene schema (units = feet; x: west(-) to east(+), z: north(-) to south(+), room centered at 0,0):
{"room":{"w":10,"l":12,"h":9,"wallColor":"#f5f5dc","floorColor":"#b08968","light":"warm|white"},
 "objects":[{"id":"tbl_1","type":"table|sofa|bed|lamp|plant|cupboard|chair|tv|bookshelf|rug|fan|painting|window|door","wall":"west|east|north|south (windows/doors/paintings only)","pos":[x,z],"color":"#hex","rot":0}]}
Keep existing objects unless asked to change/remove. Never output code or markdown."""

TYPES = {"table": ["table", "mez"], "sofa": ["sofa", "couch"], "bed": ["bed", "palang", "bistar"],
         "lamp": ["lamp", "batti"], "plant": ["plant", "paudha", "gamla"],
         "cupboard": ["cupboard", "almirah", "wardrobe"], "chair": ["chair", "kursi"], "tv": ["tv", "television", "telly"], "bookshelf": ["bookshelf", "book shelf", "shelf"],
         "rug": ["rug", "carpet", "kaleen"], "fan": ["fan", "pankha"], "painting": ["painting", "frame", "photo", "tasveer", "poster"],
         "window": ["window", "khidki"], "door": ["door", "darwaza", "darwaja"]}
COLORS = {"blue": "#8fb8de", "neela": "#8fb8de", "red": "#c0392b", "laal": "#c0392b", "green": "#7fb069",
          "hara": "#7fb069", "white": "#f4f4f0", "safed": "#f4f4f0", "yellow": "#e9c46a", "peela": "#e9c46a",
          "pink": "#f4a6c0", "gulabi": "#f4a6c0", "grey": "#9aa0a6", "gray": "#9aa0a6", "brown": "#8b5a2b",
          "wooden": "#8b5a2b", "wood": "#8b5a2b", "black": "#2b2b2b", "kala": "#2b2b2b"}
WALLS = {"west": "west", "east": "east", "north": "north", "south": "south", "left": "west", "right": "east"}
WALLED, FLAT = ("window", "door", "painting"), ("rug", "fan")
SLOTS = [(0, 0), (-4, -5), (4, -5), (-4, 5), (4, 5), (0, -5), (0, 5), (-3, -3), (3, -3), (-3, 3), (3, 3), (0, -4), (0, 4), (4, 0), (-4, 0)]

DEFAULT = {"room": {"w": 10, "l": 12, "h": 9, "wallColor": "#f5f5dc", "floorColor": "#b08968", "light": "warm", "asked": []}, "objects": []}


def clean(scene):
    s = {"room": dict(DEFAULT["room"]), "objects": []}
    try:
        s["room"].update({k: v for k, v in scene.get("room", {}).items() if k in s["room"]})
        for k in ("w", "l", "h"):
            s["room"][k] = max(4, min(40, float(s["room"][k])))
        for i, o in enumerate(scene.get("objects", [])[:40]):
            if o.get("type") in TYPES:
                p = o.get("pos") or [0, 0]
                s["objects"].append({"id": str(o.get("id", f"o{i}")), "type": o["type"], "wall": o.get("wall"),
                                     "pos": [float(p[0]), float(p[1])], "color": o.get("color"), "rot": float(o.get("rot", 0))})
    except Exception as e:
        log.warning("scene clean failed: %s", e)
        return DEFAULT
    return s


DEVA = {"सोफा": "sofa", "सोफ़ा": "sofa", "टेबल": "table", "मेज़": "table", "मेज": "table", "डाइनिंग": "dining",
        "बेड": "bed", "पलंग": "bed", "लैंप": "lamp", "लैम्प": "lamp", "लेम्प": "lamp", "पौधा": "plant", "पौधे": "plant", "प्लांट": "plant",
        "गमला": "plant", "अलमारी": "cupboard", "कबर्ड": "cupboard", "वार्डरोब": "cupboard", "कुर्सी": "chair", "चेयर": "chair",
        "खिड़की": "window", "विंडो": "window", "दरवाज़ा": "door", "दरवाजा": "door", "डोर": "door",
        "नीला": "blue", "नीले": "blue", "ब्लू": "blue", "लाल": "red", "रेड": "red", "हरा": "green", "हरे": "green", "ग्रीन": "green",
        "सफेद": "white", "सफ़ेद": "white", "व्हाइट": "white", "पीला": "yellow", "पीले": "yellow", "येलो": "yellow", "गुलाबी": "pink",
        "पिंक": "pink", "ग्रे": "grey", "स्लेटी": "grey", "भूरा": "brown", "ब्राउन": "brown", "काला": "black", "काले": "black", "ब्लैक": "black",
        "लकड़ी": "wooden", "वुडन": "wooden", "दीवार": "wall", "वॉल": "wall", "वाल": "wall", "पश्चिम": "west", "वेस्ट": "west",
        "पूर्व": "east", "ईस्ट": "east", "उत्तर": "north", "नॉर्थ": "north", "दक्षिण": "south", "साउथ": "south",
        "बाएं": "left", "बायें": "left", "बाईं": "left", "लेफ्ट": "left", "दाएं": "right", "दायें": "right", "राइट": "right",
        "हटा": "hata", "निकाल": "hata", "शिफ्ट": "shift", "सरका": "shift", "मूव": "move", "रूम": "room", "बाई": "by", "एक्स": "x",
        "वार्म": "warm", "ग्यारह": "11", "चौदह": "14", "पंद्रह": "15", "सोलह": "16", "बारह": "12", "दस": "10", "नौ": "9", "आठ": "8",
        "टीवी": "tv", "टेलीविजन": "tv", "बुकशेल्फ": "bookshelf", "किताबों की अलमारी": "bookshelf", "शेल्फ": "shelf", "कालीन": "rug", "गलीचा": "rug", "रग": "rug", "कार्पेट": "carpet", "पंखा": "fan", "फैन": "fan", "फ्रेम": "frame", "पेंटिंग": "painting", "तस्वीर": "tasveer", "फोटो": "photo", "पोस्टर": "poster", "वाली": "wali", "वाला": "wali", "वाले": "wali", "दूसरी": "second", "दूसरा": "second", "पहली": "first", "पहला": "first", "आखिरी": "last", "आखरी": "last", "आगे": "aage", "पीछे": "peeche", "खिसका": "shift", "एल ई डी": "led", "एलईडी": "led", "लाइट्स": "lights", "लाइटिंग": "lighting", "लाइट": "light", "रोशनी": "roshni", "गर्म": "warm", "रंग": "rang", "कलर": "color", "बीच": "center", "मध्य": "center", "सेंटर": "center", "सात": "7", "छह": "6", "पांच": "5", "बीस": "20"}


def normalize(text):
    t = text.lower().translate(str.maketrans("०१२३४५६७८९", "0123456789"))
    for k in sorted(DEVA, key=len, reverse=True):
        t = t.replace(k, f" {DEVA[k]} ")
    return re.sub(r"\s+", " ", t)


NAMES = {"table": "table", "sofa": "sofa", "bed": "bed", "lamp": "lamp", "plant": "plant", "cupboard": "almirah",
         "chair": "chair", "window": "khidki", "door": "darwaza", "tv": "TV", "bookshelf": "bookshelf", "rug": "kaleen", "fan": "pankha", "painting": "painting"}


def follow_up(s, skip=()):
    """Ask each follow-up at most once, so the assistant never nags."""
    r = s["room"]
    asked = r.get("asked")
    asked = ["light"] if asked is True else asked if isinstance(asked, list) else []
    r["asked"] = asked
    have = {o["type"] for o in s["objects"]}
    if "light" not in asked and s["objects"]:
        asked.append("light")
        return "Kya lighting warm rakhu ya white LED?"
    for ty in ("sofa", "lamp", "plant", "chair", "table", "rug", "tv", "bookshelf", "painting", "fan"):
        if ty not in have and ty not in skip and ty not in asked:
            asked.append(ty)
            return f"Kya main ek {NAMES[ty]} bhi rakh doon?"
    return "Aur kuch badalna hai?"


SEL = re.compile(r"\b(?:(center|centre|left|right|west|east|north|south|aage|peeche)\s+(?:wali|wala|wale|vali|vala)|(first|second|last|pehli|pehla|doosri|doosra|akhri))\b")
DIRS = r"left|right|west|east|north|south|aage|peeche|forward|back"
ADD = r"banao|daal|dal |add|insert|lagao|बनाओ|डाल|ऐड|जोड़|naya|\bnew\b|\bek\b"


def free_slot(objs, n):
    solid = [o["pos"] for o in objs if o["type"] not in WALLED + FLAT]
    for sx, sz in SLOTS:
        if all((sx - p[0]) ** 2 + (sz - p[1]) ** 2 >= 9 for p in solid):
            return [sx, sz]
    return list(SLOTS[n % len(SLOTS)])


def pick(objs, ty, sel):
    c = [o for o in objs if o["type"] == ty]
    if not c:
        return None
    if sel in ("center", "centre"):
        return min(c, key=lambda o: o["pos"][0] ** 2 + o["pos"][1] ** 2)
    if sel in ("left", "west"):
        return min(c, key=lambda o: o["pos"][0])
    if sel in ("right", "east"):
        return max(c, key=lambda o: o["pos"][0])
    if sel in ("north", "aage"):
        return min(c, key=lambda o: o["pos"][1])
    if sel in ("south", "peeche"):
        return max(c, key=lambda o: o["pos"][1])
    if sel in ("first", "pehli", "pehla"):
        return c[0]
    if sel in ("second", "doosri", "doosra"):
        return c[1] if len(c) > 1 else c[-1]
    return c[-1]


def rule_based(text, scene):
    """Offline Hinglish/Devanagari parser (demo fallback) with replies that describe what changed."""
    t, s = normalize(text), clean(scene)
    sm = SEL.search(t)
    sel = (sm.group(1) or sm.group(2)) if sm else None
    t = SEL.sub(" ", t)  # "center wali table" selects an object; it is not a direction or a placement
    ch = []
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|by|bai|\*)\s*(\d+(?:\.\d+)?)", t)
    if m:
        s["room"]["w"], s["room"]["l"] = float(m.group(1)), float(m.group(2))
        ch.append(f"{s['room']['w']:g} by {s['room']['l']:g} ka room bana diya")
    light_intent = bool(re.search(r"\bled\b|\blights?\b|lighting|roshni", t))
    if light_intent:
        white = bool(re.search(r"white|\bled\b|cool", t))
        s["room"]["light"] = "white" if white else "warm"
        s["room"]["asked"] = list(set((s["room"].get("asked") if isinstance(s["room"].get("asked"), list) else []) + ["light"]))
        ch.append("lighting white LED kar di" if white else "lighting warm kar di")
    col = None if light_intent else next((v for k, v in COLORS.items() if k in t), None)
    found = [ty for ty, words in TYPES.items() if any(w in t for w in words)]
    added, centered, removed = False, bool(re.search(r"center|centre", t)), []
    explicit_shift = bool(re.search(r"shift|move|sarka|khisk", t))
    has_dir, add_intent = bool(re.search(DIRS, t)), bool(re.search(ADD, t))
    remove = re.search(r"hata|remove|delete|nikal", t) and not explicit_shift
    wall = next((v for k, v in WALLS.items() if re.search(rf"\b{k}\b", t)), None)
    for ty in found:
        nm, objs = NAMES[ty], s["objects"]
        exists = any(o["type"] == ty for o in objs)
        movable = ty not in WALLED
        if remove:
            o = pick(objs, ty, sel)
            if o:
                objs.remove(o)
                removed.append(ty)
                ch.append(f"{nm} hata diya")
        elif col and exists and re.search(r"kar do|kar de|karo|badal|change|कर दो|कर दें|बदल", t) and not add_intent:
            targets = [pick(objs, ty, sel)] if sel else [o for o in objs if o["type"] == ty]
            for o in targets:
                o["color"] = col
            added = True
            ch.append(f"{nm} ka rang badal diya")
        elif exists and movable and (explicit_shift or (has_dir and not add_intent)):
            o = pick(objs, ty, sel)
            dx = -2 if re.search(r"left|west", t) else 2 if re.search(r"right|east", t) else 0
            dz = -2 if re.search(r"north|aage|forward", t) else 2 if re.search(r"south|peeche|back", t) else 0
            o["pos"] = [o["pos"][0] + dx, o["pos"][1] + dz]
            d = "left" if dx < 0 else "right" if dx > 0 else "aage" if dz < 0 else "peeche"
            ch.append(f"{nm} ko {d} khisaka diya")
        else:
            added = True
            n = len(objs)
            free_center = not any(x["pos"] == [0, 0] and x["type"] not in WALLED + FLAT for x in objs)
            pos = [0, 0] if (ty in FLAT or (centered and movable and free_center)) else free_slot(objs, n)
            o = {"id": f"{ty[:3]}_{n + 1}", "type": ty, "wall": None, "pos": pos, "color": col, "rot": 0}
            if not movable:
                o["wall"], o["pos"] = wall or {"window": "west", "painting": "north", "door": "south"}[ty], [0, 0]
            objs.append(o)
            ch.append(f"ek {nm} add kar diya")
    if col:
        wall_intent = re.search(r"(wall|deewar)\s*(ka|ki|ke)?\s*(color|colour|rang)|(color|colour|rang).*wall|paint", t)
        if wall_intent or not found:
            s["room"]["wallColor"] = col
            ch.append("deewar ka rang badal diya")
        elif "floor" in t or "farsh" in t:
            s["room"]["floorColor"] = col
            ch.append("farsh ka rang badal diya")
        elif found and not added:
            for o in s["objects"]:
                if o["type"] == found[-1]:
                    o["color"] = col
    if not ch:
        return s, "Samajh nahi aaya, kripya dobara boliye. Jaise: ek 10 by 12 ka room banao."
    return s, "Ho gaya! " + ", ".join(ch) + ". " + follow_up(s, removed)


GNANI_HDR = lambda: {"X-API-Key-ID": E("X_API_KEY_ID", "")}


async def prisma_stt(data: bytes, filename: str) -> str:
    """Prisma v3.0 REST (verified: docs.gnani.ai quick-start). Clips must be <=30s."""
    if not E("X_API_KEY_ID"):
        raise RuntimeError("Prisma not configured")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(E("PRISMA_ENDPOINT", "https://api.vachana.ai/stt/v3"), headers=GNANI_HDR(),
                         files={"audio_file": (filename, data, "audio/wav")},
                         data={"model": "prisma-v3.0", "language_code": E("STT_LANG", "indic-auto")})
        r.raise_for_status()
        return r.json()["transcript"]


async def evon_scene(text: str, scene: dict):
    """Evon has no Gnani-hosted REST API. Point EVON_ENDPOINT at your own OpenAI-compatible
    server (vLLM/TGI serving the Evon weights). Blank -> offline rules."""
    url = E("EVON_ENDPOINT")
    if not url:
        raise RuntimeError("Evon not configured")
    body = {"model": E("EVON_MODEL", "evon"), "temperature": 0.1,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": json.dumps({"scene": scene, "command": text}, ensure_ascii=False)}]}
    hdr = {"Authorization": "Bearer " + E("EVON_API_KEY")} if E("EVON_API_KEY") else {}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=body, headers=hdr)
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"]
    j = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    return clean(j["scene"]), str(j.get("reply", "Ho gaya."))


async def timbre_tts(text: str):
    """Timbre v2.5 REST (verified): returns raw binary WAV."""
    if not E("X_API_KEY_ID"):
        raise RuntimeError("Timbre not configured")
    body = {"text": text, "voice": E("TTS_VOICE", "Nalini"), "model": "timbre-v2.5", "language": E("TTS_LANG", "hi-IN"),
            "speed": 1.0, "audio_config": {"sample_rate": 48000, "num_channels": 1, "sample_width": 2,
                                           "encoding": "linear_pcm", "container": "wav"}}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(E("TIMBRE_ENDPOINT", "https://api.vachana.ai/api/v1/tts/inference"),
                         json=body, headers={**GNANI_HDR(), "Content-Type": "application/json"})
        r.raise_for_status()
        return base64.b64encode(r.content).decode(), "audio/wav"


@app.get("/api/status")
def status():
    return {"prisma": bool(E("X_API_KEY_ID")), "timbre": bool(E("X_API_KEY_ID")), "evon": bool(E("EVON_ENDPOINT"))}


@app.post("/api/turn")
async def turn(audio: UploadFile | None = File(None), text: str = Form(""), scene: str = Form("{}")):
    used, sc = {}, json.loads(scene or "{}")
    if audio:
        try:
            text, used["stt"] = await prisma_stt(await audio.read(), audio.filename or "a.wav"), "prisma"
        except Exception as e:
            log.warning("STT fallback: %s", e)
            used["stt"] = "browser"
            used["stt_error"] = str(e)[:160]
    if not text.strip():
        return {"transcript": "", "scene": clean(sc), "reply": "", "audio": None, "used": used}
    try:
        new, reply = await evon_scene(text, clean(sc))
        used["llm"] = "evon"
    except Exception as e:
        log.warning("LLM fallback: %s", e)
        new, reply = rule_based(text, sc)
        used["llm"] = "demo-rules"
    audio_b64, mime = None, None
    try:
        audio_b64, mime = await timbre_tts(reply)
        used["tts"] = "timbre"
    except Exception as e:
        log.warning("TTS fallback: %s", e)
        used["tts"] = "browser"
    return {"transcript": text, "scene": new, "reply": reply, "audio": audio_b64, "mime": mime, "used": used}


app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")
