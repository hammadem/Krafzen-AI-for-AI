"""Centralized logging + Sentry integration."""
import logging
import structlog
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
    """Initialize Sentry with structured logging integration."""
    if dsn:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,        
            event_level=logging.ERROR  
        )

        sentry_sdk.init(
            dsn=dsn,
            integrations=[sentry_logging],
            traces_sample_rate=1.0,
        )
