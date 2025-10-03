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

def generate_random_password(length=12): # Increased length for security
    """Generates a random, secure password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

@receiver(post_save, sender=Member)
def create_user_for_member(sender, instance, created, **kwargs):
    """
    Signal to create a User, link it to a new Member, and SMS the password
    using Twilio, after formatting the phone number to E.164.
    """
    if not created:
        return # Only run when a Member object is first created

    # Prevents infinite loop if the Member object's 'user' field is saved *after* creation
    # Also handles cases where the user might have been created manually.
    if instance.user:
        return

    # 1. Determine Username and Check for Existing User
    # Assumes phone_number is the unique identifier for the User model
    username = instance.phone_number 
    if User.objects.filter(username=username).exists():
        logger.warning(f"User creation skipped: User with phone number '{username}' already exists.")
        return

    # 2. Format Phone Number for Twilio (E.164 Standard)
    raw_phone_number = instance.phone_number
    
    # a. Remove any spaces or dashes from the raw number
    formatted_number = raw_phone_number.replace(" ", "").replace("-", "")
    
    # b. Apply Ethiopian E.164 formatting (+251...)
    if formatted_number.startswith('09'):
        # e.g., '0911...' -> '+251911...'
        formatted_number = '+251' + formatted_number[1:]
    elif formatted_number.startswith('9') and len(formatted_number) == 9:
        # e.g., '911...' (9 digits) -> '+251911...'
        formatted_number = '+251' + formatted_number
    elif formatted_number.startswith('+251'):
        # Already in correct E.164 format, do nothing
        pass
    else:
        # If the format is still invalid, stop the process and log it
        logger.error(f"INVALID PHONE FORMAT for SMS: {raw_phone_number}. Cannot send SMS/create user.")
        return

    # 3. Handle Password Generation and SMS Sending
    password = generate_random_password()
    
    try:
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            raise EnvironmentError("Twilio credentials are not fully set in settings.")

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message_body = f"""እንኳን ደህና መጡ!
የመግቢያ መረጃዎ:
የተጠቃሚ ስም: {username}
የይለፍ ቃል: {password}
በመጀመሪያው ሎግኢን የይለፍ ቃልዎን እንዲቀይሩ እንመክራለን።"""
        
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=formatted_number # 👈 የተስተካከለውን ቁጥር ይጠቀማል
        )
        
        logger.info(f"SMS successfully sent to {formatted_number} with SID: {message.sid}")
        
        # 4. Create the User (ONLY if SMS was successfully initiated)
        user = User.objects.create_user(
            username=username,
            email=instance.email if instance.email else '', # Use email if available
            password=password
        )

        # 5. Link the User to the Member profile and SAVE (CRITICAL FIX)
        # CRITICAL FIX: Temporarily disconnect the signal to prevent infinite recursion
        post_save.disconnect(create_user_for_member, sender=Member)
        
        instance.user = user
        # This instance.save() would re-trigger the signal without the disconnect.
        instance.save() 
        
        # Reconnect the signal immediately
        post_save.connect(create_user_for_member, sender=Member)
        
        logger.info(f"Created and linked user '{username}' for member '{instance.full_name}'.")
        
    except Exception as e:
        logger.error(f"TWILIO SMS OR USER CREATION FAILED for {username}: {e}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"User account for '{username}' was NOT created due to failure.")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
