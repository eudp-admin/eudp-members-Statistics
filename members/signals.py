from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member

@receiver(post_save, sender=Member)
def create_user_for_member(sender, instance, created, **kwargs):
    """
    Signal to create a User whenever a new Member is created.
    """
    if created:
        # We use the phone number as the username for simplicity.
        # You can change this to email or another unique field.
        username = instance.phone_number
        
        # Check if a user with this username already exists
        if not User.objects.filter(username=username).exists():
            # Create a simple default password. 
            # The user should be forced to change this on first login.
            password = "password123" # Warning: In a real system, generate a random password
            
            user = User.objects.create_user(
                username=username,
                password=password
            )
            
            # Optional: You can link the user to the member profile if needed
            instance.user = user
            instance.save()
            
            print(f"Created a new user '{username}' for member '{instance.full_name}'")