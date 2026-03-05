

# helpers.py 
import random
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_otp():
    """Generate a 6-digit OTP code."""
    return str(random.randint(100000, 999999))

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_otp_email(new_email, otp_code):
    """Send Verification code email to the new email address."""
    try:
        subject = 'Your Verification Code for Email Change'
        text_content = f'Your Verification code is: {otp_code}'
        
        # Enhanced and modern styled HTML content
        html_content = f'''
        <div style="font-family: Arial, sans-serif; padding: 0; margin: 0; background-color: #f4f4f4; width: 100%; height: 100%; padding-top: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);">
                
                <!-- Header section with gradient background -->
                <div style="background: linear-gradient(135deg, #3a1c71 0%, #d76d77 50%, #ffaf7b 100%); color: white; padding: 20px; text-align: center;">
                    <h1 style="font-size: 24px; margin: 0;">Email Verification</h1>
                </div>
                
                <!-- Body content -->
                <div style="padding: 30px; text-align: center; color: #333;">
                    <p style="font-size: 18px; margin-bottom: 20px;">Hi,</p>
                    <p style="font-size: 16px; margin-bottom: 20px;">Please use the verification code below to complete your email change request:</p>
                    
                    <!-- OTP code box -->
                    <p style="font-size: 32px; font-weight: bold; margin-bottom: 30px; color: #3a1c71; border: 2px dashed #d76d77; padding: 10px 20px; display: inline-block;">
                        {otp_code}
                    </p>

                    <p style="font-size: 14px; color: #666;">This code is valid for a limited time. If you didn't request this, please ignore this email.</p>
                </div>
                
                <!-- Footer with support contact -->
                <div style="background-color: #f4f4f4; padding: 20px; text-align: center; color: #666; font-size: 14px;">
                    <p>If you have any questions, contact us at <a href="mailto:support@san-tandorglobal.online" style="color: #3a1c71; text-decoration: none;">Support@san-tandorglobal.online</a></p>
                    <p>© 2025 SANTANDER, All Rights Reserved.</p>
                </div>
            </div>
        </div>
        '''
        
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [new_email]
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        
        logger.info(f"Verification Code email sent to {new_email}")
    except Exception as e:
        logger.error(f"Error sending Verification Code email: {str(e)}")
        raise e

