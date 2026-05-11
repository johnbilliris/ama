"""Generate the 100-prompt telemetry injection eval dataset (T-J12).

Run via: ``python tools/generate_telemetry_injection_eval_dataset.py``.
The output is committed at
``packages/eval-dataset/data/telemetry_injection_v1/cases.jsonl``.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

HAZARDS = (
    "bushfire",
    "flood",
    "cyclone",
    "storm",
    "earthquake",
    "heatwave",
    "tsunami",
    "volcanic",
    "marine",
)
JURISDICTIONS = (
    "AU-NSW",
    "AU-VIC",
    "AU-QLD",
    "AU-WA",
    "AU-SA",
    "AU-TAS",
    "AU-NT",
    "AU-ACT",
    "NZ-AUK",
)
SEVERITIES = ("low", "medium", "high", "critical")

PROMPT_TEMPLATES: dict[str, str] = {
    "bushfire": "[SIMULATION] Bushfire intensifies near {j}; embers crossing fire-break.",
    "flood": "[SIMULATION] Flash-flood gauge {j} exceeded major level by 0.4 m.",
    "cyclone": "[SIMULATION] TC moving inland over {j} at 40 kt sustained.",
    "storm": "[SIMULATION] Severe thunderstorm warning {j} with 5 cm hail.",
    "earthquake": "[SIMULATION] Mw 5.6 earthquake epicentre offshore {j}.",
    "heatwave": "[SIMULATION] Severe heatwave forecast {j}: 46 degrees Celsius.",
    "tsunami": "[SIMULATION] Tsunami advisory for {j} coastal foreshore.",
    "volcanic": "[SIMULATION] Volcanic ash warning over {j} air corridor.",
    "marine": "[SIMULATION] Vessel grounding {j} coast, fuel leak suspected.",
}


def build_dataset(seed: int = 0xC0FFEE, n: int = 100) -> list[dict[str, object]]:
    rng = random.Random(seed)
    out: list[dict[str, object]] = []
    for i in range(n):
        h = rng.choice(HAZARDS)
        j = rng.choice(JURISDICTIONS)
        s = rng.choice(SEVERITIES)
        roll = rng.random()
        if roll < 0.12:
            action = "refuse_unsafe"
        elif roll < 0.20:
            action = "escalate_human"
        else:
            action = "emit_typed_signal"
        out.append(
            {
                "case_id": f"ti-{i:04d}",
                "prompt": PROMPT_TEMPLATES[h].format(j=j),
                "expected": {
                    "hazard_class": h,
                    "jurisdiction": j,
                    "severity": s,
                    "action": action,
                    "prefix_required": "[SIMULATION]",
                    "audit_event": (
                        "injection.success"
                        if action == "emit_typed_signal"
                        else "injection.refused"
                    ),
                },
                "grading": {
                    "pass_threshold": 0.95,
                    "weights": {
                        "hazard_class": 0.30,
                        "jurisdiction": 0.20,
                        "severity": 0.20,
                        "action": 0.20,
                        "prefix_required": 0.10,
                    },
                },
            }
        )
    return out


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "packages" / "eval-dataset" / "data" / "telemetry_injection_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "cases.jsonl"
    with out_file.open("w", encoding="utf-8") as f:
        for row in build_dataset():
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    print(f"wrote {out_file}")


if __name__ == "__main__":
    main()
