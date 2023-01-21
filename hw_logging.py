import sys


def get_logger(level, color=None):
    if color is None:
        color = sys.stdout.isatty()

    try:
        from loguru import logger as loguru_logger
        loguru_logger.remove()
        loguru_logger.add(
            sys.stdout,
            colorize=color,
            format="<level>{level} {message}</level>",
            level=level)
        return loguru_logger
    except ImportError:
        import logging as python_logging
        python_logging.basicConfig(level=level)
        return python_logging.getLogger()
