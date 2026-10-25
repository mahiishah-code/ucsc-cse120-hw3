# SlugGuide

SlugGuide is an accessibility-first companion that helps students navigate both the physical environment and the school day. It combines a live camera/vision pipeline, a context-aware personal companion, and a reusable open-source decision engine.

## Architecture

The system is structured as follows:

Camera
↓
FastAPI backend
↓
SlugGuide Core
↓
Google GenAI SDK + Gemma model
↓
Priority engine, navigation decisions, and audio routing
↓
Frontend companion UI

### Where Gemma is used

SlugGuide uses the current official Google GenAI SDK and a configurable Gemma model name from the environment. The backend sends a live camera frame to the model, and the model produces structured JSON describing the scene, relevant objects, hazards, direction, and distance. That output is normalized and passed into SlugGuide Core.

For the current live environment, the backend honors `GEMMA_MODEL` if set, otherwise it defaults to a supported Gemma model identifier in the Google GenAI ecosystem. This keeps the implementation aligned with the official SDK rather than inventing a custom API.

### What SlugGuide Core does

SlugGuide Core is the reusable open-source layer that turns raw AI perception into accessibility decisions. It:

- normalizes multimodal scene data
- identifies hazards and relevant objects
- computes tier and mode (ALERT / GUIDE / ASSIST / SILENCE)
- applies cooldown and duplicate suppression
- attaches navigation relevance and confidence
- prepares audio output decisions and guidance

This is the part designed to be reusable by other projects and developers.

## Why Gemma?

Gemma is the best fit for this project because it enables genuine multimodal understanding from a real camera frame. SlugGuide is not just a static dashboard or keyword matcher; it can reason over general scenes and general objects such as stairs, doors, chairs, sofas, bicycles, poles, signs, pathways, vehicles, laptop screens, and more.

This makes the system practical for real-world accessibility tasks, not just a demo subset of predefined alerts.

## Why Open Source?

SlugGuide Core is intentionally isolated and model-agnostic where practical so that the same logic can be reused in other accessibility or navigation toolchains. With a clean Python package, documentation, and clear interfaces, the project is ready for open-source contribution and external experimentation.

## DigitalOcean Deployment

This project is structured to be deployable on DigitalOcean via Docker. The backend reads the API key from the environment variable `GEMINI_API_KEY` and runs as a FastAPI service. The frontend is a separate Vite client that connects to the backend via HTTP and the same local network or reverse proxy configuration.

## Live AI vs Demo Mode

The app distinguishes live AI from demo mode explicitly:

- If `GEMINI_API_KEY` or `GOOGLE_API_KEY` is configured, the backend attempts a real multimodal analysis through the Google GenAI SDK.
- If the key is missing or the request fails, the app falls back to Demo Mode and clearly labels the output as demo data.
- Demo Mode is a fallback and not a substitute for live AI.

## Tracking the hackathon prize goals

This implementation supports both key tracks:

1. Best Use of Gemma
   - live camera frame input
   - multimodal scene understanding through the official Google GenAI SDK and a Gemma model
   - structured output for hazards and objects
   - natural-language companion context integration

2. DigitalOcean / Best Open-Source AI Project
   - reusable core package under `slug-guide-core/`
   - open-source licensing and documentation
   - Docker deployment files
   - environment-variable-driven backend configuration

## Getting started

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
export GEMMA_MODEL="gemma-3-27b-it"
uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5174
```

## Demo flow

1. Start SlugGuide.
2. Camera begins.
3. Point at an ordinary scene.
4. Gemma identifies relevant objects.
5. No important hazard → SILENCE.
6. Point at stairs or an obstacle.
7. Gemma identifies it.
8. Priority engine produces ALERT.
9. User hears a short warning.
10. Ask "What's around me?"
11. Ask "What's my next class?"
12. Ask "Take me there."
13. Navigation mode starts.

## Open-source core

The reusable core lives under `slug-guide-core/` and includes:

- `priority_engine.py`
- `vision_schema.py`
- `navigation.py`
- `audio_router.py`

It can be imported into other Python projects and extended for different accessibility or navigation contexts.
