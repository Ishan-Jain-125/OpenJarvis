
import os

from openjarvis.core.config import load_config
from openjarvis.engine.openai_compat_engines import OpenAICompatEngine
from openjarvis.server.app import create_app
from openjarvis.server.auth_middleware import check_bind_safety

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "10000"))

PROVIDER_URL = os.environ["FREELLMAPI_BASE_URL"].rstrip("/")
PROVIDER_KEY = os.environ["FREELLMAPI_API_KEY"]
APP_KEY = os.environ["OPENJARVIS_API_KEY"]
MODEL = os.getenv("JARVIS_MODEL", "auto")

check_bind_safety(HOST, api_key=APP_KEY)

config = load_config()

engine = OpenAICompatEngine(
    host=PROVIDER_URL,
    api_key=PROVIDER_KEY,
    timeout=600.0,
)

cors_raw = os.getenv("OPENJARVIS_CORS_ORIGINS", "").strip()
cors_origins = (
    [x.strip() for x in cors_raw.split(",") if x.strip()]
    if cors_raw
    else config.server.cors_origins
)

# Use the official OpenJarvis application and frontend.
app = create_app(
    engine,
    MODEL,
    engine_name="openai-compat",
    config=config,
    api_key=APP_KEY,
    cors_origins=cors_origins,
)
