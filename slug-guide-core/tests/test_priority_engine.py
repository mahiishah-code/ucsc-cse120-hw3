import unittest

from priority_engine import PriorityEngine


class PriorityEngineTests(unittest.TestCase):
    def test_prioritizes_critical_hazards(self):
        engine = PriorityEngine()
        scene = {
            "scene": "building entrance",
            "objects": [{"label": "door", "direction": "right", "distance": "near", "hazard": False}],
            "hazards": [{"label": "stairs", "direction": "center", "distance": "near", "severity": "critical"}],
            "tier": 1,
            "message": "Stop — stairs ahead.",
        }
        result = engine.decide(scene)
        self.assertEqual(result["mode"], "ALERT")
        self.assertEqual(result["tier"], 1)
        self.assertEqual(result["object"], "stairs")

    def test_suppresses_duplicates_with_cooldown(self):
        engine = PriorityEngine(cooldown_seconds=60)
        first = engine.decide({"scene": "hallway", "objects": [], "hazards": [{"label": "chair", "direction": "left", "distance": "near", "severity": "medium"}]})
        second = engine.decide({"scene": "hallway", "objects": [], "hazards": [{"label": "chair", "direction": "left", "distance": "near", "severity": "medium"}]})
        self.assertEqual(first["mode"], "GUIDE")
        self.assertEqual(second["mode"], "SILENCE")


if __name__ == "__main__":
    unittest.main()
