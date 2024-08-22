import logging


def setup_logger(app_name: str, env: str) -> logging.Logger:
    # Create a logger
    logger = logging.getLogger(app_name)

    # Create a console handler
    ch = logging.StreamHandler()

    # Set log level based on the environment
    if env.lower() == "dev":
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(ch)

    return logger
