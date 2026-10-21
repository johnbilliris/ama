"""Communication Agent - multilingual alert generation, content safety, AIIMS approval, multi-channel dissemination."""

from communication.config import CommunicationConfig
from communication.runtime import build_application

__version__ = "0.1.0"
__all__ = ["CommunicationConfig", "build_application"]
