import os
from dotenv import load_dotenv
import queue


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_QUEUE = queue.Queue()

LOG_FILE = "logs/bioz/runtime.log"
CALLBACK_URL = os.getenv("CALLBACK_URL")

SECRET_PATH = "secrets/"
os.makedirs(SECRET_PATH, exist_ok=True)

# Edit .gitignore if change these path
AUTH0_TOKEN_PATH = "secrets/auth0-token.json"
GOOGLEAPI_TOKEN_PATH = "secrets/google-api-token.pickle"

AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

FEEDBACK_TIMEOUT = 5
RESULT_TIMEOUT = 180
VIDEO_AGE_LIMIT = 100  # days

DEBUG_CHANNEL = os.getenv("DEBUG_CHANNEL")

EASYFRENCH_PLAYLISTID = "PLA5UIoabheFMYWWnGFFxl8_nvVZWZSykc"
