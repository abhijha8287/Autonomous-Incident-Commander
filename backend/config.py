import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SPLUNK_HOST = os.getenv("SPLUNK_HOST", "localhost")
SPLUNK_PORT = int(os.getenv("SPLUNK_PORT", "8089"))
SPLUNK_USERNAME = os.getenv("SPLUNK_USERNAME", "admin")
SPLUNK_PASSWORD = os.getenv("SPLUNK_PASSWORD", "")
SPLUNK_MODE = os.getenv("SPLUNK_MODE", "simulator")  # "live" | "simulator"

DATABASE_URL = "sqlite:///./incidents.db"
PDF_OUTPUT_DIR = "./reports_output"
LLM_MODEL = "claude-sonnet-4-6"
