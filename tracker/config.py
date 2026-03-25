import os
import re
import logging
from dotenv import load_dotenv

load_dotenv()

# --- Email ---
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
NOTIFY_TO = os.getenv("NOTIFY_TO", "")

# --- Price range ---
PRICE_MIN = float(os.getenv("PRICE_MIN", "16.0"))
PRICE_MAX = float(os.getenv("PRICE_MAX", "20.0"))

# --- Mercadona warehouse (affects prices and availability) ---
# Common values: vlc1 (Valencia), mad1 (Madrid), bcn1 (Barcelona)
MERCADONA_WAREHOUSE = os.getenv("MERCADONA_WAREHOUSE", "vlc1")

# --- Search query ---
QUERY = "salmón ahumado"


def validate():
    missing = [k for k, v in {
        "GMAIL_USER": GMAIL_USER,
        "GMAIL_APP_PASSWORD": GMAIL_APP_PASSWORD,
        "NOTIFY_TO": NOTIFY_TO,
    }.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Variables de entorno requeridas no definidas: {', '.join(missing)}\n"
            "Copia .env.example a .env y rellena los valores."
        )


def parse_price(raw: str) -> float | None:
    """Convierte '9,95 €', '9.95', '9,95€/ud' → 9.95. Devuelve None si falla."""
    cleaned = re.sub(r"[^\d,.]", "", raw.strip()).replace(",", ".")
    parts = cleaned.split(".")
    if len(parts) > 2:
        # Separador de miles: "1.299.95" → "1299.95"
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        value = float(cleaned)
        return value if value > 0 else None
    except ValueError:
        return None


def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    from logging.handlers import RotatingFileHandler
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "tracker.log"),
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
