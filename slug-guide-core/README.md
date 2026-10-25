# SlugGuide Core

SlugGuide Core is the reusable Python decision layer for accessibility-first AI navigation systems.

## Architecture

The core sits between perception and action. It accepts a structured vision scene from a multimodal model and outputs a decision that can drive the UI, audio guidance, and navigation state.

The pipeline is:

VISION → hazard / relevance analysis → priority engine → output mode → frontend / navigation / audio

## Input schema

```json
{
  "scene": "building entrance",
  "objects": [
    {
      "label": "stairs",
      "direction": "center",
      "distance": "near",
      "hazard": true,
      "confidence": 0.96
    }
  ],
  "hazards": [
    {
      "label": "stairs",
      "direction": "center",
      "distance": "near",
      "severity": "critical",
      "confidence": 0.96
    }
  ],
  "tier": 1,
  "message": "Stop — stairs ahead."
}
```

## Output schema

```json
{
  "mode": "ALERT",
  "tier": 1,
  "object": "stairs",
  "hazard": true,
  "direction": "center",
  "distance": "near",
  "message": "Stop — stairs ahead.",
  "confidence": 0.96,
  "cooldown": 20.0,
  "suppressed": false,
  "navigation_relevant": true
}
```

## Features

- severity-based hazard prioritization
- duplicate alert suppression with cooldown
- navigation relevance labeling
- confidence tracking
- model-agnostic design where practical
- audio-routing support

## Example usage

```python
from slug_guide_core import PriorityEngine

engine = PriorityEngine()
result = engine.decide({
    "scene": "indoor room",
    "objects": [{"label": "sofa", "direction": "center", "distance": "near", "hazard": False, "confidence": 0.9}],
    "hazards": [],
    "tier": 3,
    "message": "",
})
print(result)
```

## Extending the core

Other developers can reuse the module for:

- richer navigation reasoning
- additional multilingual output
- custom hazard scoring logic
- audio policy routing
- other accessibility or wayfinding products
