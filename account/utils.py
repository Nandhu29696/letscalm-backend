from django.core.mail import EmailMessage
import os
import random, string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.core.mail import send_mail
from .models import EmailOTP


 
class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            from_email=os.environ.get('FROM_MAIL'),
            to=[data['to_email']]
        )
        email.send()
        
        
def generate_otp(length=6):
    return "".join(random.choice(string.digits) for _ in range(length))

def create_and_send_otp(user, purpose="register"):
    length = int(getattr(settings, "OTP_LENGTH", 6))
    otp_value = generate_otp(length=length)
    expiry_seconds = int(getattr(settings, "OTP_EXPIRY_SECONDS", 300))
    expires_at = timezone.now() + timedelta(seconds=expiry_seconds)

    otp = EmailOTP.objects.create(user=user, otp=otp_value, purpose=purpose, expires_at=expires_at)

    subject = f"Your {purpose} OTP code"
    message = f"Your OTP is: {otp_value}. It will expire in {expiry_seconds//60} minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient = [user.email]

    send_mail(subject, message, from_email, recipient, fail_silently=False)
    return otp

