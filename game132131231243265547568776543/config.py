from pathlib import Path
import os

BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"
LOGS_DIR = BASE_DIR / "logs"

IMAGES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/game_club")
APP_TITLE = "Настольные игры - Клуб любителей"
APP_VERSION = "1.0.0"
CAPTCHA_PARTS = 4
CAPTCHA_PATH = str(IMAGES_DIR / "captcha_full.png")

ACCESS_LEVELS = {
    'Администратор': 1,
    'Пользователь': 2,
}

MAX_LOGIN_ATTEMPTS = 3
LOG_FILE = str(LOGS_DIR / "app.log")