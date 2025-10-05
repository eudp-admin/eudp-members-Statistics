from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# =========================================================================
# 1. MEMBER MODEL
# =========================================================================

# Define choices globally or immediately before the model for better readability

REGION_CHOICES = [
    ('አዲስ አበባ', 'አዲስ አበባ'),
    ('አማራ', 'አማራ'), # <-- Addressed: Added Amhara region
    ('ኦሮሚያ', 'ኦሮሚያ'),
    ('ትግራይ', 'ትግራይ'),
    ('ደቡብ ኢትዮጵያ', 'ደቡብ ኢትዮጵያ'),
    ('ደቡብ ምዕራብ ኢትዮጵያ', 'ደቡብ ምዕራብ ኢትዮጵያ'),
    ('ሶማሌ', 'ሶማሌ'),
    ('ጋምቤላ', 'ጋምቤላ'),
    ('ሐረር', 'ሐረር'),
    ('ድሬዳዋ', 'ድሬዳዋ'),
    ('ቤኒሻንጉል ጉሙዝ', 'ቤኒሻንጉል ጉሙዝ'),
    ('ሲዳማ', 'ሲዳማ'),
    ('አፋር', 'አፋር'),
]

EDUCATION_CHOICES = [
    ('መሰረታዊ ትምህርት', 'መሰረታዊ ትምህርት'),
    ('ሁለተኛ ደረጃ', 'ሁለተኛ ደረጃ'),
    ('ዲፕሎማ', 'ዲፕሎማ'),
    ('ዲግሪ', 'ዲግሪ'),
    ('ማስተርስ', 'ማስተርስ'),
    ('ዶክትሬት (PhD)', 'ዶክትሬት (PhD)'),
    ('ሌላ', 'ሌላ'),
]


class Member(models.Model):
    # --- Basic Information ---
    full_name = models.CharField(max_length=255, verbose_name="ሙሉ ስም")
    gender = models.CharField(max_length=10, choices=[('Male', 'ወንድ'), ('Female', 'ሴት')], verbose_name="ጾታ")
    date_of_birth = models.DateField(verbose_name="የትውልድ ቀን")
    photo = models.ImageField(upload_to='member_photos/', null=True, blank=True, verbose_name="ፎቶግራፍ")

    # --- Contact Information ---
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="ስልክ ቁጥር")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="ኢሜይል")
    address_region = models.CharField(
        max_length=100,
        verbose_name="ክልል",
        choices=REGION_CHOICES
    )
    address_zone = models.CharField(max_length=100, verbose_name="ዞን")
    address_woreda = models.CharField(max_length=100, verbose_name="ወረዳ")
    address_kebele = models.CharField(max_length=100, verbose_name="ቀበሌ")

    # --- Party Information ---
    membership_id = models.CharField(max_length=100, unique=True, blank=True, verbose_name="የአባልነት መለያ ቁጥር")
    membership_level = models.CharField(max_length=50, choices=[('Full', 'ሙሉ አባል'), ('Supporter', 'ደጋፊ')], verbose_name="የአባልነት ደረጃ")
    party_role = models.CharField(max_length=100, blank=True, null=True, verbose_name="በፓርቲ ውስጥ ያለ ኃላፊነት")
    join_date = models.DateField(auto_now_add=True, verbose_name="የተቀላቀለበት ቀን")

    # --- Other Information ---
    education_level = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="የትምህርት ደረጃ",
        choices=EDUCATION_CHOICES
    )
    profession = models.CharField(max_length=100, blank=True, null=True, verbose_name="የስራ መስክ")

    # --- System Fields ---
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="የአባልነት ሁኔታ (Active)")

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        # Check if this is a new object being created (has no pk yet)
        if not self.pk:
            # --- 1. Generate Membership ID FIRST ---
            current_year = datetime.now().year
            
            # --- FIX: Removed .upper() to match Amharic keys and ensured all keys are correct ---
            region = self.address_region
            region_code_map = {
                'አማራ': 'AMH',
                'ኦሮሚያ': 'ORO',
                'ትግራይ': 'TIG',
                'አዲስ አበባ': 'AA',
                'ድሬዳዋ': 'DD',
                'ደቡብ ኢትዮጵያ': 'SOET',
                'ደቡብ ምዕራብ ኢትዮጵያ': 'SWET',
                'ሐረር': 'HAR',
                'አፋር': 'AFR',
                'ሶማሌ': 'SOM',
                'ጋምቤላ': 'GAM',
                # --- FIX: Corrected spelling to match REGION_CHOICES ---
                'ቤኒሻንጉል ጉሙዝ': 'BEN', 
                'ሲዳማ': 'SID',
            }
            # Use .get() for safe retrieval, defaulting to 'OTH'
            region_code = region_code_map.get(region, 'OTH')
            
            # Find the highest existing number for this region and year
            last_member = Member.objects.filter(
                address_region=self.address_region, 
                join_date__year=current_year
            ).order_by('pk').last()
            
            new_seq_num = 1
            if last_member and last_member.membership_id:
                try:
                    # Extract the sequence number part (the last component after the last hyphen)
                    last_seq_num = int(last_member.membership_id.split('-')[-1])
                    new_seq_num = last_seq_num + 1
                except (ValueError, IndexError):
                    # If parsing fails, fall back to starting sequence number 1
                    pass
            
            self.membership_id = f"{region_code}-{current_year}-{new_seq_num:04d}"

        # --- 2. Call the original save method NOW ---
        # Now that the membership_id is set (for new members) or unchanged (for updates), we save.
        super().save(*args, **kwargs)

        # --- 3. Create and Link User AFTER the member is saved ---
        # This part only runs if it's a new member (not self.pk means it was new before the super().save()) 
        # OR if the user was somehow unlinked (not self.user).
        # We need to ensure we don't try to link a user on every update, but only when a user is missing.
        if not self.user:
            username = self.phone_number
            if not User.objects.filter(username=username).exists():
                # print(f"Attempting to create user '{username}' for new member.") # Removed print for clean code
                password = "password123" # WARNING: Change this in production code!
                try:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email=self.email if self.email else ""
                    )
                    self.user = user
                    # Save again just to update the user link
                    super().save(update_fields=['user'])
                    # print(f"Successfully created and linked user '{username}'.") # Removed print for clean code
                except Exception as e:
                    # print(f"CRITICAL ERROR during user creation in model: {e}") # Removed print for clean code
                    pass # Silently fail or log in a real application
            else:
                # print(f"User '{username}' already exists. Linking.") # Removed print for clean code
                try:
                    self.user = User.objects.get(username=username)
                    super().save(update_fields=['user'])
                except User.DoesNotExist:
                    print(f"User '{username}' was supposed to exist but not found. Something is wrong.") # Removed print for clean code
                    
# =========================================================================
# 2. MEETING MODEL
# =========================================================================

class Meeting(models.Model):
    title = models.CharField(max_length=255, verbose_name="የስብሰባው ርዕስ")
    description = models.TextField(blank=True, null=True, verbose_name="አጭር መግለጫ")
    meeting_date = models.DateTimeField(verbose_name="የስብሰባው ቀን እና ሰዓት")
    location = models.CharField(max_length=255, verbose_name="የስብሰባው ቦታ")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ፈጣሪ")
    # related_name is necessary when using a ManyToManyField through a custom model
    attendees = models.ManyToManyField(Member, through='Attendance', related_name='attended_meetings', verbose_name="ተሰብሳቢዎች")

    def __str__(self):
        return self.title

# =========================================================================
# 3. ATTENDANCE MODEL
# =========================================================================

class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="አባል")
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name="ስብሰባ")
    attended_at = models.DateTimeField(auto_now_add=True, verbose_name="የተገኘበት ሰዓት")

    class Meta:
        unique_together = ('member', 'meeting') # Ensure a member can't be marked as attendee twice for the same meeting
        verbose_name_plural = "Attendances" # Better plural name in the admin

    def __str__(self):
        return f"{self.member.full_name} attended {self.meeting.title}"
# =========================================================================
# 4. ANNOUNCEMENT MODEL
# =========================================================================

class Announcement(models.Model):
    title = models.CharField(max_length=255, verbose_name="ርዕስ")
    content = models.TextField(verbose_name="ይዘት")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ደራሲ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta: # <-- FIX: Added Meta class for ordering
        ordering = ['-created_at'] # Show the newest announcements first
