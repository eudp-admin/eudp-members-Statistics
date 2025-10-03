# signals.py
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member
from twilio.rest import Client
import string
import random
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def generate_random_password(length=12): # Use a secure length
    """Generates a random, secure password."""
    # Using letters, digits, and punctuation for high security
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

@receiver(post_save, sender=Member)
def create_user_for_member(sender, instance, created, **kwargs):
    """
    Signal to create a User, link it to a new Member, and SMS the password
    using Twilio.
    """
    if not created:
        return # Only run when a Member object is first created

    # Prevents infinite loop if the Member object's 'user' field is saved *after* creation
    if instance.user:
        return

    # 1. Determine Username and Check for Existing User
    # Assumes phone_number is the unique identifier for the User model
    username = instance.phone_number 
    if User.objects.filter(username=username).exists():
        logger.warning(f"User creation skipped: User with phone number '{username}' already exists.")
        return

    # 2. Handle Password Generation and SMS Sending
    password = generate_random_password()
    
    # --- Twilio SMS Integration ---
    try:
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            raise EnvironmentError("Twilio credentials are not fully set in settings.")

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # IMPORTANT: Ensure the phone_number is in E.164 format (e.g., +251911123456)
        to_phone_number = instance.phone_number
        
        message_body = f"""እንኳን ደህና መጡ!
የመግቢያ መረጃዎ:
የተጠቃሚ ስም: {username}
የይለፍ ቃል: {password}
በመጀመሪያው ሎግኢን የይለፍ ቃልዎን ይቀይሩ።"""
        
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        logger.info(f"SMS successfully sent to {to_phone_number} with SID: {message.sid}")
        
        # 3. Create the User (ONLY if SMS was successfully initiated)
        user = User.objects.create_user(
            username=username,
            email=instance.email if instance.email else '',
            password=password
        )

        # 4. Link the User to the Member profile and SAVE (CRITICAL FIX IMPLEMENTATION)
        # CRITICAL FIX: To prevent an infinite recursion loop when instance.save() is called,
        # we temporarily disconnect and reconnect the signal.
        post_save.disconnect(create_user_for_member, sender=Member)
        
        instance.user = user
        instance.save()
        
        # Reconnect the signal immediately
        post_save.connect(create_user_for_member, sender=Member)
        
        logger.info(f"Created and linked user '{username}' for member '{instance.full_name}'.")
        
    except Exception as e:
        logger.error(f"TWILIO SMS OR USER CREATION FAILED for {username}: {e}")
        # Log a critical failure but do NOT create the user if the initial
        # communication (SMS) failed, as the member would be locked out.
        # If the member object was saved but the user wasn't, an admin would need to intervene.
        print(f"User account for '{username}' was NOT created due to failure.")
