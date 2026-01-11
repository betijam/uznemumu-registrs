import os
import resend
from typing import List
from pydantic import EmailStr
import logging

logger = logging.getLogger(__name__)

# Configure Resend
resend.api_key = os.getenv("RESEND_API_KEY")

async def send_email(subject: str, email_to: List[str], html_content: str):
    if not resend.api_key:
        logger.warning("RESEND_API_KEY is not set. Email not sent.")
        return

    from_email = os.getenv("MAIL_FROM", "onboarding@resend.dev") # Default Resend testing domain
    
    # If using production domain, change default above to 'info@company360.lv'
    # But for testing without domain verification, 'onboarding@resend.dev' works (only to your own email)

    try:
        params = {
            "from": from_email,
            "to": email_to,
            "subject": subject,
            "html": html_content,
        }

        email = resend.Emails.send(params)
        logger.info(f"Email sent: {email}")
    except Exception as e:
        logger.error(f"Failed to send email via Resend: {e}")
        # Re-raise or handle appropriately
        raise e

async def send_verification_email(email: EmailStr, token: str):
    frontend_url = os.getenv("FRONTEND_URL", "https://company360.lv")
    link = f"{frontend_url}/verify-email?token={token}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ background-color: #2563EB; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 20px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Verificē savu e-pastu</h2>
            <p>Sveiki!</p>
            <p>Paldies, ka reģistrējies Company360. Lai pabeigtu reģistrāciju, lūdzu, apstiprini savu e-pasta adresi.</p>
            
            <a href="{link}" class="button">Apstiprināt e-pastu</a>
            
            <p style="margin-top: 20px;">Vai arī kopē šo saiti savā pārlūkā:<br>
            <a href="{link}">{link}</a></p>
            
            <div class="footer">
                <p>Ja tu neveici reģistrāciju, vari ignorēt šo e-pastu.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Convert EmailStr to string
    await send_email("Verificē savu e-pastu - Company360", [str(email)], body)

async def send_reset_password_email(email: EmailStr, token: str):
    frontend_url = os.getenv("FRONTEND_URL", "https://company360.lv")
    link = f"{frontend_url}/reset-password?token={token}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ background-color: #2563EB; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 20px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Paroles atjaunošana</h2>
            <p>Mēs saņēmām pieprasījumu atjaunot tavu Company360 paroli.</p>
            
            <a href="{link}" class="button">Atjaunot paroli</a>
            
            <p>Saite ir aktīva 1 stundu.</p>
            
            <p style="margin-top: 20px;">Vai arī kopē šo saiti savā pārlūkā:<br>
            <a href="{link}">{link}</a></p>
            
            <div class="footer">
                <p>Ja tu nepieprasīji paroles maiņu, lūdzu, ignorē šo e-pastu.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    await send_email("Atjaunot paroli - Company360", [str(email)], body)
