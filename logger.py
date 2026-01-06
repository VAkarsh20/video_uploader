import logging
import sys
import time


class Logger:
    HEADER = "\033[95m"
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"

    def __init__(self, log_file_path, level=logging.INFO):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(level)

        # Ensure no duplicate handlers if called multiple times
        if not self._logger.handlers:
            # File handler for plain text logging
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(level)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    @staticmethod
    def phase(name):
        print(f"\n{Logger.BOLD}{Logger.HEADER}{'='*60}{Logger.ENDC}")
        print(f"{Logger.BOLD}{Logger.HEADER} PHASE: {name.upper()} ".center(60, " "))
        print(f"{Logger.BOLD}{Logger.HEADER}{'='*60}{Logger.ENDC}")
        # Also log to file without colors
        logging.getLogger(__name__).info(f"PHASE: {name.upper()}")

    @staticmethod
    def info(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Logger.INFO}• {msg}{Logger.ENDC}")
        logging.getLogger(__name__).info(msg)

    @staticmethod
    def step(msg, x, y):
        # Aligned coordinate logging for scannability
        print(
            f"    {Logger.ENDC}└─ {msg:<25} @ {Logger.BOLD}({int(x)}, {int(y)}){Logger.ENDC}"
        )
        logging.getLogger(__name__).info(f"STEP: {msg} @ ({int(x)}, {int(y)})")

    @staticmethod
    def success(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Logger.SUCCESS}✔ {msg}{Logger.ENDC}")
        logging.getLogger(__name__).info(f"SUCCESS: {msg}")

    @staticmethod
    def warning(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Logger.WARNING}⚠ {msg}{Logger.ENDC}")
        logging.getLogger(__name__).warning(msg)

    @staticmethod
    def error(msg, exc_info=False):
        print(f"[{time.strftime('%H:%M:%S')}] {Logger.FAIL}✗ {msg}{Logger.ENDC}")
        logging.getLogger(__name__).error(msg, exc_info=exc_info)

    @staticmethod
    def debug(msg):
        # Debug messages are only logged to file by default, unless level is set lower
        logging.getLogger(__name__).debug(msg)

    @staticmethod
    def progress(current, total, bar_length=20):
        percent = float(current) / total
        arrow = "#" * int(round(percent * bar_length) - 1) + ">"
        spaces = " " * (bar_length - len(arrow))
        sys.stdout.write(
            f"    {Logger.INFO}Progress: [{arrow}{spaces}] {current}/{total} Clips{Logger.ENDC}"
        )
        sys.stdout.flush()
        if current == total:
            print()
            logging.getLogger(__name__).info(
                f"Progress: {current}/{total} Clips (Complete)"
            )
