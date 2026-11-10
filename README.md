# Eklavya — The Real-Time Voice-to-Code 3D Spatial Blueprint Engine

> **Speak a room into existence — in English, Hindi, or Hinglish.**
> Eklavya turns unstructured, code-mixed voice instructions into an interactive 3D WebGL viewport with a dynamic, real-time ₹ material cost estimator, and voices feedback right back to you.

***Built solo for The Great Indian AI Internship Challenge 2026 by Gnani.ai***  
`#GnaniAI` `#GreatIndianAIInternshipChallenge` `#IndicAI` `#BuildInPublic`

---

## ⚡ The Core Problem
Traditional 3D layout and digital planning suites (AutoCAD, Blender) suffer from incredibly steep learning curves. Local Indian carpenters, designers, small-scale contractors, and everyday families cannot easily translate the layout in their head into a digital blueprint or accurate price quotation. 

Worse, standard global tools completely fail to interpret how real Indians naturally communicate: a fluid mix of Hindi and English (**Hinglish**).

---

## ✨ System Capabilities
* **Instant Conversational Compilation:** Say *"Ek 10x12 ka room banao, west wall pe wooden window daalo, center mein dining table daal do"* and watch the geometry render immediately.
* **Persistent Voice Modifications:** Perform sequential, multi-turn updates on the fly: *"Center wali table ko left shift karo"*, *"Wall ka color blue kar do"*, *"White LED lights rakh... wait, warm yellow lagao."*
* **14 Native Parametric Components:** Deep support for standard architectural meshes: `table`, `sofa`, `bed`, `chair`, `lamp`, `plant`, `almirah`, `TV`, `bookshelf`, `rug`, `ceiling fan`, `painting`, `window`, and `door`.
* **Automated B2B Financial Matrix:** Computes dynamic cost adjustments (flooring square-footage, volume of paint, asset valuations) generating a live printable quotation.
* **Bi-directional Vocal Loop:** The assistant voices a context-aware confirmation out loud after processing every modification layer.

---

## 🏗️ Technical Architecture & Pipeline Flow

Use code with caution.
Browser mic ──► WAV 16kHz ──► FastAPI /api/turn ──► Gnani Prisma (STT)
│
▼
Scene Compiler: Evon (if configured) or Local Hybrid Parser
│  (Outputs Validated JSON Scene Graph)
▼
Gnani Timbre (TTS) ──► Audio Track Streaming
│
Browser: Vanilla Three.js rendering Engine · ₹ Estimate Matrix · Subtitle Canvas · Pipeline Status

### 🧠 The Engineering Edge: Deterministic Graph Mutation
The language layer **never emits raw code strings or executes `eval()`**, neutralizing hallucination vulnerabilities entirely. Instead, it serves as a strict **State Mutator** changing parameters within a validated JSON scene graph. Pre-built Three.js components listen to this stream to safely handle spatial rendering updates—guaranteeing the frontend canvas can never crash during production runs.

### 🛡️ Production-Grade Resilience & Fallbacks
* **Speech-to-Text:** If the network drops or Prisma encounters an edge case, the system gracefully falls back to the native browser Web Speech API.
* **Text-to-Speech:** If the TTS inference loop hits a timeout limit, browser speech synthesis components take over audio track delivery.

---

## 🔌 Gnani AI Microservice Integrations

| Runtime Stage | Sovereign Model | System Implementation Engine |
| :--- | :--- | :--- |
| **Hear** | **Prisma v3.0** (STT, `indic-auto`) | Ingests 16 kHz raw browser audio bytes ➜ Dispatches to `POST /stt/v3` ➜ Returns clean code-mixed Hinglish transcript. |
| **Reply** | **Timbre v2.5** (TTS) | Takes parsed status string text ➜ Dispatches to `POST /api/v1/tts/inference` ➜ Feeds live output audio buffer back to browser track. |

> 💡 **Architectural Note on Evon Integration:** Evon runs completely open-weights. While the base deployment operates an advanced, highly calibrated localized Hinglish parser to match resource parameters, the platform includes a plug-and-play **Evon Adapter** (`evon_scene` inside `main.py`). Simply map `EVON_ENDPOINT` to your custom hosted server frame (vLLM / OpenAI-compatible layer) and the system transitions to full LLM-driven reasoning instantly. The UI terminal live-tracks which core engine is handling runtime calculation frames.

---

## 🛠️ Rapid Local Deployment

### 1. Initialize Python Environment
```bash
git clone <this-repo> && cd <this-repo>
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials
Duplicate `.env.example` to `.env` and map your developer portal access key:
```text
X_API_KEY_ID=your_official_gnani_token_here
```

### 3. Launch Development Server
```bash
uvicorn main:app --reload
```
Open **Google Chrome** to `http://localhost:8000` to boot the application dashboard layer. Verify microservice health states anytime at `http://localhost:8000/api/status`.

---

## 🚀 Future Roadmap
* Upgrade standard turn-based audio pipeline to continuous streaming STT over stateful WebSockets.
* Integrate full production Evon framework hosted directly via high-throughput **vLLM** configurations.
* Implement native export structures for `.glTF` and `.obj` universal formats to bridge with professional CAD platforms.
* Expand spatial mapping dictionaries to deep vernacular Southern/Eastern linguistic matrices.
* Add an immersive Mobile AR preview layer using standard WebXR frames.

---

## 👥 Production Team
* **Solo Software Engineer:** Prashi Jain  
* **Academic Institution:** IIT Madras  
* **Location Core:** Udaipur, India  
* *Responsibility Scope:* End-to-end conceptual design, FastAPI core network engine, Gnani API interface layers, local spatial parsing logic matrices, Vanilla Three.js rendering canvas, UI/UX graphic framework design, and public presentation asset production.

---

## 🖥️ Core Development Stack
* **Backend Core:** `Python` | `FastAPI` | `httpx` | `websockets`
* **Visual Engine:** `Vanilla Three.js` | `HTML5 Canvas API` | `WebGL`
* **Hardware Routing:** `Web Audio API` | `MediaRecorder`
* **AI Foundational Processing:** `Gnani Prisma v3.0` | `Gnani Timbre v2.5
