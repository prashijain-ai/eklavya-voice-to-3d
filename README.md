# Project Eklavya – Voice-to-3D Spatial Blueprint Engine
Speak Hinglish → **Gnani Prisma** (STT) → **Gnani Evon** (parametric JSON scene compiler) → live Three.js room + ₹ estimate → **Gnani Timbre** speaks back.

## Run
pip install -r requirements.txt && cp .env.example .env
uvicorn main:app --reload   # open http://localhost:8000

## Architecture
Browser (16kHz WAV via Web Audio) → FastAPI /api/turn → Prisma → Evon (scene JSON, validated by `clean()`) → Timbre → browser.
Evon never emits code; it mutates a validated JSON scene graph rendered by pre-built Three.js components (no eval, no crashes).
Fallbacks (offline rules / browser TTS) keep the demo alive if an API call fails; the UI shows which engine handled each stage.

## Roles
Solo builder: <your name> – everything.
