"""Custom logger wrapper with structlog."""
from structlog import get_logger

logger = get_logger("krafzen")
