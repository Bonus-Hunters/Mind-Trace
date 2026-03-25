import secrets
import smtplib
import ssl
from email.message import EmailMessage
from core.config_loader import ConfigLoader
import bcrypt
from core.database.repos import EmployeesRepository
from core.database.postgresDatabase import PostgresDatabase


def get_email_domain(email: str) -> str:

    if not email or "@" not in email == 0:
        return None

    parts = email.rsplit("@", 1)
    if len(parts) != 2 or not parts[1]:
        return None

    return parts[1].strip().lower()


# generate a random 6 digits OTP
def generate_OTP() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def send_email(sender_email: str, reciever_email: str, sender_password: str) -> bool:

    # basic validation
    if not sender_email or "@" not in sender_email:
        return False

    if not reciever_email or "@" not in reciever_email:
        return False

    if not sender_password:
        return False

    otp = generate_OTP()
    subject = "Mind Trace Verification Code"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: bold;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .content p {{
                color: #333333;
                font-size: 16px;
                line-height: 1.6;
                margin: 0 0 20px 0;
            }}
            .otp-box {{
                background-color: #f9f9f9;
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
                display: inline-block;
            }}
            .otp-code {{
                font-size: 36px;
                font-weight: bold;
                color: #667eea;
                letter-spacing: 4px;
                font-family: 'Courier New', monospace;
            }}
            .expiry {{
                color: #999999;
                font-size: 14px;
                margin-top: 20px;
            }}
            .footer {{
                background-color: #f4f4f4;
                padding: 20px;
                text-align: center;
                color: #666666;
                font-size: 12px;
                border-top: 1px solid #e0e0e0;
            }}
            .warning {{
                color: #d9534f;
                font-size: 13px;
                margin-top: 15px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Mind Trace</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p> 
                    Thanks for signing up! Before we start, 
                    we just need to confirm it's really you.
                    Please write the attached OTP below 
                    in your IDE.
                </p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp}</div>
                </div>
                
                <p class="expiry">⏱️ This code will expire in 10 minutes.</p>
                <p class="warning">⚠️ Do not share this code with anyone.</p>
            </div>
            <div class="footer">
                <p>If you did not request this code, please ignore this email.</p>
                <p>&copy; 2026 Mind-Trace. All rights reserved.</p>
            </div>
            </p>
        </div>
    </body>
    </html>
    """

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = reciever_email
    msg["Subject"] = subject
    msg.set_content(html_body, subtype="html")

    domain = sender_email.rsplit("@", 1)[1].lower()
    provider_map = {
        "gmail.com": ("smtp.gmail.com", 465, "ssl"),
        "outlook.com": ("smtp.office365.com", 587, "starttls"),
        "yahoo.com": ("smtp.mail.yahoo.com", 465, "ssl"),
        "icloud.com": ("smtp.mail.me.com", 587, "starttls"),
    }

    host, port, mode = provider_map.get(domain, (f"smtp.{domain}", 465, "ssl"))

    try:
        if mode == "ssl":
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP_SSL(host, port, context=context) as smtp:
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)
        return True, otp
    except Exception as e:
        print(f" --- Error: Couldn't send email: {e}")
        return False


def hash_password(password: str):
    password = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def get_current_author(email: str) -> str:
    try:
        db = PostgresDatabase()
        employeeRepo = EmployeesRepository(db.get_session_maker())
        employee = employeeRepo.get_by_email(email)
        if employee:
            return employee
        return False
    except Exception as e:
        print
        return False
    finally:
        del db
        del employeeRepo
