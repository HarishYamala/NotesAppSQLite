import os

# Secret key for sessions
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

MAIL_CONFIG = {
    "MAIL_SERVER": "smtp.gmail.com",
    "MAIL_PORT": 465,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "harishyamala2002@gmail.com",
    "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD", "ftbchvsbsueojnzz"),
    "BASE_URL": "https://xxxx.ngrok-free.app"  # change after deployment
}
