"""Evacuation Agent — ``python -m evacuation`` entrypoint.

Starts the FastAPI health server on port 8082 (configurable via ``PORT``
environment variable) and optionally launches the Service Bus consumer
for processing handoff events.
"""

from __future__ import annotations

import logging
import os

import uvicorn
from evacuation.agent import EvacuationAgent, create_app
from evacuation.config import EvacuationConfig

_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_console = logging.StreamHandler()
_console.setFormatter(_fmt)
root = logging.getLogger()
root.addHandler(_console)
root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

_PORT = int(os.environ.get("PORT", "8082"))
_config = EvacuationConfig()
_agent = EvacuationAgent(config=_config)

app = create_app(agent=_agent, config=_config)

logger.info("Evacuation Agent starting on port %d", _PORT)
uvicorn.run(app, host="0.0.0.0", port=_PORT, log_level="info")
