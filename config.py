# config.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret")

MAIL_CONFIG = {
    "MAIL_SERVER": "smtp.gmail.com",
    "MAIL_PORT": 465,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "harishyamala2002@gmail.com",
    "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD")  # ✅ PythonAnywhere reads this
}

