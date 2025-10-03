from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member

@receiver(post_save, sender=Member)
def create_or_update_user_for_member(sender, instance, created, **kwargs):
    """
    Creates or updates a User when a Member is created.
    This is a more robust version to handle potential issues.
    """
    username = instance.phone_number

    if created:
        # This is a NEW member.
        if User.objects.filter(username=username).exists():
            print(f"ERROR: A user with username '{username}' already exists. Cannot create a new one.")
            return

        print(f"Attempting to create a new user for member: {instance.full_name} with username: {username}")
        
        password = "password123"
        
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=instance.email if instance.email else ""
            )
            
            # Link the new user to the member profile IMMEDIATELY
            instance.user = user
            # We need to save the instance again, but prevent an infinite loop
            # by disconnecting the signal temporarily.
            post_save.disconnect(create_or_update_user_for_member, sender=Member)
            instance.save()
            post_save.connect(create_or_update_user_for_member, sender=Member)

            print(f"SUCCESS: Created and linked user '{username}' for member '{instance.full_name}'")

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"CRITICAL ERROR during user creation for {username}: {e}")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
    # This part handles updates, though not strictly necessary for creation, it's good practice.
    else:
        # This is an EXISTING member being updated.
        # Ensure the user object is linked if it exists.
        if not instance.user and User.objects.filter(username=username).exists():
            user_to_link = User.objects.get(username=username)
            instance.user = user_to_link
            post_save.disconnect(create_or_update_user_for_member, sender=Member)
            instance.save()
            post_save.connect(create_or_update_user_for_member, sender=Member)
            print(f"Linked existing user '{username}' to updated member '{instance.full_name}'")
