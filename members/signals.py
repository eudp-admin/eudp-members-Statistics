from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member

@receiver(post_save, sender=Member)
def create_user_for_member(sender, instance, created, **kwargs):
    """
    Creates a User with a default password whenever a new Member is created.
    This is a temporary solution until the Ethio Telecom SMS API is integrated.
    """
    if created:
        # Check if a user is already linked to this member instance.
        # This prevents the signal from running multiple times.
        if hasattr(instance, 'user') and instance.user is not None:
            return

        username = instance.phone_number
        
        # Check if a user with this username (phone number) already exists.
        if User.objects.filter(username=username).exists():
            # If it exists, we can try to link it, but for now, we'll just stop
            # to avoid creating a duplicate.
            print(f"User with username '{username}' already exists. Skipping user creation.")
            return
        
        # Use a default, predictable password.
        # This will be replaced with a password sent via SMS in the future.
        password = "password123"
        
        # Create the new user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=instance.email if instance.email else "" # Also save the email if provided
        )
        
        # Link the new user to the member profile and save the member instance again
        instance.user = user
        instance.save()
        
        print(f"Created user '{username}' with a default password. SMS integration is pending.")
