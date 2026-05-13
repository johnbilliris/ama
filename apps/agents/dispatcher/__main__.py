"""Sub-agent dispatcher entrypoint — uvicorn runner on port 8080.

The agents Container App invokes this module as ``python -m dispatcher``.
Port matches ``infra/main.bicep`` (``agentsContainerApp.targetPort = 8080``).
"""

from __future__ import annotations

import os

import uvicorn

from dispatcher.agent import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=os.getenv("LOG_LEVEL", "info"))
