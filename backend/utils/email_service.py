import os
import resend
from fastapi import HTTPException

class EmailService:
    def __init__(self):
        resend.api_key = os.getenv("EMAIL_KEY")

    async def send_otp_email(self, email: str, otp: str) -> bool:
        print(email, otp)
        try:
            params: resend.Emails.SendParams = {
                "from": "admin <noreply@abtinfi.ir>",
                "to": [email],
                "subject": "OTP Code",
                "html": f"""
                <h1>Your OTP Code</h1>
                <p>Your one-time password is: <strong>{otp}</strong></p>
                <p>This code will expire in 5 minutes.</p>
                """
            }
            response = resend.Emails.send(params)
            print(response)
            return True
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Failed to send email")

email_service = EmailService()
