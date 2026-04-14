from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
FERNET_KEY = os.environ["FERNET_KEY"]
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///yahoo_email.db")
IMAP_TIMEOUT = int(os.environ.get("IMAP_TIMEOUT", "10"))
