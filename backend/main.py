import base64
import json
import os
import re
import time
import urllib.request
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None

app = FastAPI(title="SlugGuide", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCHEDULE = [
    {"time": "10:00 AM", "title": "CSE 120", "location": "Engineering 2"},
    {"time": "12:30 PM", "title": "Lunch", "location": "Cowell Dining Commons"},
    {"time": "3:00 PM", "title": "ACM Meeting", "location": "Jack Baskin Engineering"},
]

TASKS = [
    "Submit CSE 120 Homework",
    "Reply to project team",
    "Review lecture notes",
]

DEMO_DETECTIONS = [
    {
        "tier": 1,
        "object": "stairs",
        "hazard": True,
        "direction": "center",
        "distance": "2 meters",
        "message": "Stop — stairs ahead.",
        "source": "demo",
    },
    {
        "tier": 2,
        "object": "obstacle",
        "hazard": True,
        "direction": "left",
        "distance": "3 meters",
        "message": "Obstacle detected — left.",
        "source": "demo",
    },
    {
        "tier": 3,
        "object": "sofa",
        "hazard": False,
        "direction": "right",
        "distance": "near",
        "message": "Sofa ahead.",
        "source": "demo",
    },
    {
        "tier": 3,
        "object": "open pathway",
        "hazard": False,
        "direction": "none",
        "distance": "unknown",
        "message": "",
        "source": "demo",
    },
]


def get_next_class():
    return SCHEDULE[0]


def get_today_response():
    return {
        "date": datetime.now().strftime("%A, %B %d"),
        "schedule": SCHEDULE,
        "tasks": TASKS,
        "next_class": get_next_class(),
        "tagline": "Navigate the world. Navigate your day.",
    }


def normalize_detection(raw: dict | None) -> dict:
    raw = raw or {}
    tier = raw.get("tier", 3)
    try:
        tier_value = int(tier)
    except (TypeError, ValueError):
        tier_value = 3
    tier_value = max(1, min(3, tier_value))

    object_name = str(raw.get("object") or raw.get("hazard") or "scene").strip() or "scene"
    hazard_value = raw.get("hazard", False)
    if isinstance(hazard_value, str):
        hazard_value = hazard_value.lower() in {"true", "yes", "hazard", "warning"}
    hazard_value = bool(hazard_value)

    direction = str(raw.get("direction") or "center").strip() or "center"
    distance = str(raw.get("distance") or "unknown").strip() or "unknown"
    message = str(raw.get("message") or "").strip()

    return {
        "tier": tier_value,
        "object": object_name.lower(),
        "hazard": hazard_value,
        "direction": direction.lower(),
        "distance": distance,
        "message": message,
        "source": raw.get("source", "live"),
    }


def demo_detection(index: int | None = None) -> dict:
    sample = DEMO_DETECTIONS[(index if index is not None else int(time.time()) // 8) % len(DEMO_DETECTIONS)]
    return normalize_detection(sample)


def parse_model_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("` ")
        cleaned = re.sub(r"^json\s*", "", cleaned, flags=re.IGNORECASE)
    data = json.loads(cleaned)
    return normalize_detection(data)


def extract_text_from_response(response) -> str:
    if hasattr(response, "text") and response.text:
        return response.text

    payload = response
    if hasattr(response, "model_dump"):
        payload = response.model_dump()

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "text" and isinstance(item, str):
                    return item
                found = walk(item)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = walk(item)
                if found:
                    return found
        return None

    text = walk(payload)
    if text:
        return text
    raise ValueError("Could not extract text from Gemini response")


def get_model_name() -> str:
    return (
        os.getenv("GEMMA_MODEL")
        or os.getenv("GEMINI_MODEL")
        or os.getenv("GOOGLE_GENAI_MODEL")
        or "gemma-4-26b-a4b-it"
    )


def has_live_ai_credentials() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def get_system_status() -> dict:
    return {
        "demo_mode": not has_live_ai_credentials(),
        "model": get_model_name(),
        "service": "slugguide",
    }


def analyze_with_gemini(image_b64: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No Gemini API key configured")
    if genai is None or types is None:
        raise RuntimeError("google-genai package not installed")

    prompt = (
        "You are SlugGuide, an accessibility assistant. "
        "Analyze the live scene from the camera for a blind or low-vision user. "
        "Return valid JSON only with keys: tier, object, hazard, direction, distance, message. "
        "tier is 1 for immediate hazards, 2 for navigation guidance, 3 for non-critical or no important issue. "
        "object should be a single important visible item such as stairs, sofa, chair, table, laptop, person, door, bicycle, vehicle, pole, wall, entrance, crosswalk, obstacle, pathway, sign, bench, curb, or scene. "
        "hazard is true only for immediate or path-blocking concerns. "
        "direction is one of left, right, center, none. "
        "distance should be a short phrase like near, 2 meters, 5 meters, unknown. "
        "message should be short and accessibility-focused and empty for non-critical scenes. "
        "Do not narrate every object. Pick only what matters most."
    )

    model_name = get_model_name()
    image_bytes = base64.b64decode(image_b64, validate=False)
    print(f"[SlugGuide] Live vision request: model={model_name}, image_bytes={len(image_bytes)}")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                ],
            )
        ],
    )

    candidate_text = extract_text_from_response(response)
    print(f"[SlugGuide] Live vision response received: {candidate_text[:220]}")
    result = parse_model_response(candidate_text)
    result["source"] = "live"
    print(f"[SlugGuide] Parsed live response: {result}")
    return result


async def analyze_image_payload(image_b64: str | None) -> dict:
    if not image_b64:
        print("[SlugGuide] No image payload received; returning idle state.")
        return {
            "tier": 3,
            "object": "open pathway",
            "hazard": False,
            "direction": "none",
            "distance": "unknown",
            "message": "No live frame available.",
            "source": "idle",
        }

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            return analyze_with_gemini(image_b64)
        except Exception as exc:
            print(f"[SlugGuide] Live AI failed with configured credentials: {exc}")
            return {
                "tier": 3,
                "object": "scene",
                "hazard": False,
                "direction": "none",
                "distance": "unknown",
                "message": "Live Gemma unavailable. Please verify API credentials and model access.",
                "source": "live_error",
            }

    print("[SlugGuide] No API key configured; demo mode enabled.")
    return {**demo_detection(), "source": "demo", "message": "Demo Mode — no Gemini API key configured."}


def answer_question(question: str, context: dict | None = None) -> str:
    q = (question or "").lower()
    context = normalize_detection(context)

    if "next class" in q or "what is my next" in q or "where is my class" in q:
        return "Your next class is CSE 120 in Engineering 2 at 10:00 AM."
    if "today" in q or "my day" in q or "schedule" in q:
        return "Today you have CSE 120 at 10:00 AM in Engineering 2, lunch at 12:30 PM at Cowell Dining Commons, and ACM Meeting at 3:00 PM in Jack Baskin Engineering."
    if "task" in q or "tasks" in q:
        return "Your tasks are to submit CSE 120 Homework, reply to your project team, and review lecture notes."
    if "leave" in q or "when should i leave" in q or "to my next class" in q:
        return "You should leave for CSE 120 in about 25 minutes to arrive on time in Engineering 2."
    if "what do you see" in q or "what is around me" in q or "around me" in q or "what is around" in q:
        if context.get("hazard") and context.get("message"):
            return f"I see {context.get('object', 'a scene')} {context.get('direction', 'ahead')}. {context.get('message')}"
        if context.get("object") and context.get("object") != "open pathway":
            return f"I see a {context.get('object')} {context.get('direction', '')}."
        return "I see an open pathway with no immediate hazards."
    if "sofa" in q or "chair" in q or "door" in q or "stairs" in q:
        if context.get("object") and q.find(context.get("object")) >= 0:
            return f"I see a {context.get('object')} {context.get('direction', 'ahead')}."
    if "hello" in q or "hi" in q:
        return "Hello. I am SlugGuide. I can tell you your next class, today's schedule, your tasks, or what is around you."
    return "I can help with your next class, today's schedule, your tasks, or what's around you."


@app.get("/")
def home():
    return {"name": "SlugGuide", "tagline": "Navigate the world. Navigate your day."}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "slugguide"}


@app.get("/api/system")
def system_status():
    return get_system_status()


@app.get("/api/today")
def today():
    return get_today_response()


@app.post("/api/tasks")
def tasks(payload: dict | None = None):
    data = payload or {}
    task = str(data.get("task") or "").strip()
    tasks_list = list(TASKS)
    if task and task not in tasks_list:
        tasks_list.append(task)
    return {"tasks": tasks_list}


@app.post("/api/ask")
def ask(payload: dict | None = None):
    data = payload or {}
    question = str(data.get("question", ""))
    context = data.get("context")
    return {"answer": answer_question(question, context=context)}


@app.post("/api/vision")
async def analyze_vision(payload: dict | None = None):
    data = payload or {}
    image_b64 = data.get("image")
    response = await analyze_image_payload(image_b64)
    return response


@app.websocket("/ws/vision")
async def vision_socket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw_message = await ws.receive_text()
            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            image_b64 = payload.get("image")
            if image_b64:
                detection = await analyze_image_payload(image_b64)
                await ws.send_json(detection)
            else:
                await ws.send_json({**demo_detection(), "source": "demo", "message": "Demo Mode — no live frame received."})
    except WebSocketDisconnect:
        await ws.close()
