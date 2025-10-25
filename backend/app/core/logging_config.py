"""Centralized logging + Sentry integration."""
import logging
import structlog
from sentry_sdk.integrations.logging import SentryLoggingIntegration
from app.core.config import settings

# Basic stdlib setup
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Structured logging
timestamper = structlog.processors.TimeStamper(fmt="iso")
pre_chain = [
    structlog.stdlib.add_log_level,
    timestamper,
]
structlog.configure(
    processors=pre_chain + [structlog.processors.JSONRenderer()],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def init_sentry(dsn: str):
    if dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            integrations=[SentryLoggingIntegration(level=logging.INFO)],
            traces_sample_rate=1.0,
        )
