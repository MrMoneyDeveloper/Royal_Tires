"""
ROLE: Core logging policy
CALLED BY: main lifespan
CALLS: Python logging configuration
DATA IN: Logger configuration, not user credentials
DATA OUT: INFO application logs; quieter httpx logs
WHY: Choose log format and levels once at startup.
SECURITY / RELIABILITY: Suppresses routine httpx URLs at INFO. This is not a universal
    redactor: callers must keep secrets out; ZendeskService separately sanitizes upstream
    errors.
FLOW: main lifespan -> this module -> Python logging configuration
"""

import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # HTTP client logs can include external URLs; business logs contain IDs only.
    logging.getLogger("httpx").setLevel(logging.WARNING)
