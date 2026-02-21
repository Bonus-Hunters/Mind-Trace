from core.database.authentication import *
from core.config_loader import ConfigLoader

config_laoder = ConfigLoader()

sender = config_laoder.get("MIND_TRACE_EMAIL")
rec_email = "nadahany505@gmail.com"
passcode = config_laoder.get("MIND_TRACE_PASSWORD")
valid = send_email(
    sender,
    rec_email,
    passcode,
)
print(f"sender: {sender}")
print(f"pass: {passcode}")
print(valid)
