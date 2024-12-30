import logging

class ColorFormatter(logging.Formatter):
    COLORS = {
        "white": "\033[97m",
        "red": "\033[91m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }

    def __init__(self, fmt, default_color="white"):
        super().__init__(fmt)
        self.default_color = self.COLORS.get(default_color.lower(), self.COLORS["white"])

    def format(self, record):
        # Use the color passed in `record.color` or fall back to the default color
        color = self.COLORS.get(getattr(record, 'color', '').lower(), self.default_color)
        msg = super().format(record)
        return f"{color}{msg}{self.COLORS['reset']}"
    
def logger_cfg(logger, debug_color="red", info_color="white"):
    logger.setLevel(logging.DEBUG)

    # File handler for debug logs
    debug_file_handler = logging.FileHandler('debug.log')
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    debug_file_handler.setFormatter(debug_file_formatter)

    # File handler for info logs
    info_file_handler = logging.FileHandler('info.log')
    info_file_handler.setLevel(logging.INFO)
    info_file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_file_handler.setFormatter(info_file_formatter)

    # Console handler for debug logs (colorized)
    console_handler_debug = logging.StreamHandler()
    console_handler_debug.setLevel(logging.DEBUG)
    console_handler_debug.setFormatter(ColorFormatter('%(levelname)s - %(message)s', default_color=debug_color))

    # Console handler for info logs (colorized)
    console_handler_info = logging.StreamHandler()
    console_handler_info.setLevel(logging.INFO)
    console_handler_info.setFormatter(ColorFormatter('%(levelname)s - %(message)s', default_color=info_color))

    # Add handlers to logger
    logger.addHandler(debug_file_handler)
    logger.addHandler(info_file_handler)
    logger.addHandler(console_handler_debug)
    logger.addHandler(console_handler_info)
