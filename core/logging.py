from loguru import logger

# Configure Loguru
logger.add(
    "logs/app.log",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    colorize=True,
    format="{time} | {level} | {message}",
)