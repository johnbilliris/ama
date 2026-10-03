"""Planning Agent entrypoint — uvicorn runner on port 8085 (R-012)."""

import os

if __name__ == "__main__":
    import uvicorn
    from planning.agent import create_app
    from planning.config import PlanningConfig

    from apps.console_logging import configure_console_logging, uvicorn_log_config

    configure_console_logging()
    _PORT = int(os.environ.get("PORT", "8085"))
    config = PlanningConfig()
    app = create_app(config=config)
    uvicorn.run(app, host="0.0.0.0", port=_PORT, log_config=uvicorn_log_config())
