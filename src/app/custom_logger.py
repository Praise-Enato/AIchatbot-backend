import json
import logging
import os


class ExtraFormatter(logging.Formatter):
    """
    Formatter that appends any non-standard LogRecord attributes
    (i.e. what you pass via extra={}) as a JSON dict.
    """

    def format(self, record: logging.LogRecord) -> str:
        # First, let the base class format the known fields.
        base = super().format(record)

        # Identify “extra” fields by subtracting standard LogRecord attributes
        standard = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "taskName",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "asctime",
        }
        extra = {key: value for key, value in record.__dict__.items() if key not in standard}
        if extra:
            try:
                extra_json = json.dumps(extra)
            except Exception:
                extra_json = str(extra)
            return f"{base} - {extra_json}"
        return base


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger that on local runs will print:
      timestamp - name - level - message - {"your":"extras"}
    In AWS Lambda (where AWS_..._FUNCTION_NAME is set) it leaves logging alone.

    Log level is controlled by the LOG_LEVEL environment variable.
    """
    logger = logging.getLogger(name)

    # Set log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    try:
        level = getattr(logging, log_level)
    except AttributeError:
        level = logging.INFO
    logger.setLevel(level)

    # If we're not in Lambda, install a console handler once
    if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ and not any(
        isinstance(h, logging.StreamHandler) for h in logger.handlers
    ):
        console = logging.StreamHandler()
        console.setLevel(level)
        fmt = "%(asctime)s - %(levelname)s - %(name)s.%(message)s"
        console.setFormatter(ExtraFormatter(fmt))
        logger.addHandler(console)
    return logger
