# signals.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member
from django.core.mail import send_mail
import string
import random
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def generate_random_password(length=12): # Increased length for better security
    """Generates a random, secure password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

@receiver(post_save, sender=Member)
def create_user_for_member(sender, instance, created, **kwargs):
    """
    Signal to create a User and link it to a new Member,
    and email the password if an email is available.
    """
    if not created:
        return # Only run when a Member object is first created

    # 1. Determine Username and Check for Existing User
    username = instance.phone_number
    if User.objects.filter(username=username).exists():
        # User with this unique identifier already exists, prevent creation.
        logger.warning(f"User creation skipped: Username '{username}' already exists.")
        return

    # 2. Handle Password Generation and Emailing
    password = generate_random_password()
    email_sent_successfully = False

    if instance.email:
        try:
            subject = 'እንኳን ወደ ፓርቲያችን በደህና መጡ! (Welcome to Our Party!)'
            message = f"""
ሰላም {instance.full_name},

የፓርቲያችን አባል ለመሆን ስለተመዘገቡ እናመሰግናለን።
የተጠቃሚ አካውንትዎ በተሳካ ሁኔታ ተፈጥሯል።

ወደ ስርዓቱ ለመግባት ይህንን መረጃ ይጠቀሙ:
የተጠቃሚ ስም (Username): {username}
የይለፍ ቃል (Password): {password}

ሎግኢን ካደረጉ በኋላ ወዲያውኑ የይለፍ ቃልዎን እንዲቀይሩ እንመክራለን።

ከሰላምታ ጋር,
የፓርቲው አስተዳደር
"""
            # Using the email keyword argument ensures it's sent as a single email.
            send_mail(
                subject, 
                message, 
                None, # Uses DEFAULT_FROM_EMAIL from settings
                [instance.email],
                fail_silently=False # Log the error if it fails
            )
            email_sent_successfully = True
            logger.info(f"Welcome email successfully sent to {instance.email}")

        except Exception as e:
            # If email fails, log it and fall back to the generic password
            password = "password123" # Fallback password
            logger.error(f"EMAIL SENDING FAILED for {instance.email}: {e}. Using default password.")
    else:
        # No email provided, use the generic fallback password
        password = "password123" 
        logger.warning(f"No email provided for {instance.full_name}. Using default password 'password123'.")

    # 3. Create the User
    user = User.objects.create_user(
        username=username,
        email=instance.email if instance.email else '',
        password=password
    )

    # 4. Link the User to the Member profile and SAVE (CRITICAL FIX)
    
    # CRITICAL FIX: Temporarily disconnect the signal to prevent infinite recursion
    post_save.disconnect(create_user_for_member, sender=Member)
    
    instance.user = user
    # Note: If your Member model has a user field, this save triggers the signal 
    # and would cause an infinite loop without the disconnect/reconnect.
    instance.save() 
    
    # Reconnect the signal immediately
    post_save.connect(create_user_for_member, sender=Member)
    
    logger.info(f"Created and linked user '{username}' for member '{instance.full_name}'.")
