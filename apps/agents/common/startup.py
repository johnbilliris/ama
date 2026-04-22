"""Agent service startup — registers background tasks like the dead-letter poller."""

from __future__ import annotations

import logging

from common.dead_letters import DeadLetterRedeliveryPoller, DeadLetterStore

logger = logging.getLogger(__name__)

_poller: DeadLetterRedeliveryPoller | None = None


async def start_background_services(
    dead_letter_store: DeadLetterStore | None = None,
    deliver_fn=None,
) -> None:
    """Start background services on agent boot."""
    global _poller
    if dead_letter_store:
        _poller = DeadLetterRedeliveryPoller(
            store=dead_letter_store,
            deliver_fn=deliver_fn,
        )
        await _poller.start()
        logger.info("Background services started")


async def stop_background_services() -> None:
    """Gracefully stop background services on shutdown."""
    global _poller
    if _poller:
        await _poller.stop()
        _poller = None
        logger.info("Background services stopped")
