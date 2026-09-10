import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # HTTP client logs can include external URLs; business logs contain IDs only.
    logging.getLogger("httpx").setLevel(logging.WARNING)
