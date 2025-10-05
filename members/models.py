from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# =========================================================================
# 1. MEMBER MODEL
# =========================================================================
class Member(models.Model):
    # There should only be ONE primary key definition, ideally at the top.
    # id = models.AutoField(primary_key=True) # Django adds this by default, so we can remove it

    # --- Basic Information ---
    full_name = models.CharField(max_length=255, verbose_name="ሙሉ ስም")
    gender = models.CharField(max_length=10, choices=[('Male', 'ወንድ'), ('Female', 'ሴት')], verbose_name="ጾታ")
    date_of_birth = models.DateField(verbose_name="የትውልድ ቀን")
    photo = models.ImageField(upload_to='member_photos/', null=True, blank=True, verbose_name="ፎቶግራፍ")

    # --- Contact Information ---
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="ስልክ ቁጥር")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="ኢሜይል")
    # Define the choices OUTSIDE the field definition
    REGION_CHOICES = [
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
    # Now, pass the variable using the 'choices' keyword
    address_region = models.CharField(
        max_length=100, 
        verbose_name="ክልል", 
        choices=REGION_CHOICES  # <-- THE FIX IS HERE
    )#
    address_zone = models.CharField(max_length=100, verbose_name="ዞን")
    address_woreda = models.CharField(max_length=100, verbose_name="ወረዳ")
    address_kebele = models.CharField(max_length=100, verbose_name="ቀበሌ")
    
    # --- Party Information ---
    membership_id = models.CharField(max_length=100, unique=True, blank=True, verbose_name="የአባልነት መለያ ቁጥር")
    membership_level = models.CharField(max_length=50, choices=[('Full', 'ሙሉ አባል'), ('Supporter', 'ደጋፊ')], verbose_name="የአባልነት ደረጃ")
    party_role = models.CharField(max_length=100, blank=True, null=True, verbose_name="በፓርቲ ውስጥ ያለ ኃላፊነት")
    join_date = models.DateField(auto_now_add=True, verbose_name="የተቀላቀለበት ቀን")
    
    # --- Other Information ---
# Define the choices OUTSIDE the field definition
    EDUCATION_CHOICES = [
        ('መሰረታዊ ትምህርት', 'መሰረታዊ ትምህርት'),
        ('ሁለተኛ ደረጃ', 'ሁለተኛ ደረጃ'),
        ('ዲፕሎማ', 'ዲፕሎማ'),
        ('ዲግሪ', 'ዲግሪ'),
        ('ማስተርስ', 'ማስተርስ'),
        ('ዶክትሬት (PhD)', 'ዶክትሬት (PhD)'),
        ('ሌላ', 'ሌላ'),
    ]
    # Now, pass the variable using the 'choices' keyword
    education_level = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="የትምህርት ደረጃ",
        choices=EDUCATION_CHOICES # <-- THE FIX IS HERE
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
        # This logic runs only when creating a NEW member for the first time
        if not self.pk:
            # 1. Get the current year
            current_year = datetime.now().year
            
            # 2. Get a 3-letter code for the region (Ensure consistent key/value case)
            region = self.address_region.upper()
            region_code = {
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
                'ቤንሻንጉል ጉሙዝ': 'BEN',
                'ሲዳማ': 'SID',
                'SOMALI': 'SOM', # Add common English names if they might be used
                'AMHARA': 'AMH',
                'OROMIA': 'ORO',
                # Add other regions as needed...
            }.get(region_name, 'OTH') # 'OTH' for other/unlisted regions

            # 3. Find the last member registered in the same year to get the next number
            # We simplify the filter here, checking only the year and region is redundant if the ID ensures uniqueness.
            # However, to ensure sequential numbering PER region/year, we keep the original intent:
             last_member_in_region_year = Member.objects.filter(
                address_region=self.address_region, 
                join_date__year=current_year
            ).order_by('pk').last()
            
            new_seq_num = 1
            if last_member_in_region_year and last_member_in_region_year.membership_id:
                try:
                    last_seq_num = int(last_member_in_region_year.membership_id.split('-')[-1])
                    new_seq_num = last_seq_num + 1
                except (ValueError, IndexError):
                    pass
            
            self.membership_id = f"{region_code}-{current_year}-{new_seq_num:04d}"

        # Call the original save method
        super().save(*args, **kwargs)

# =========================================================================
# 2. MEETING MODEL
#    (Moved outside of Member model and save method)
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
#    (Moved outside of Member model and save method)
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
    # models.py

# ... other classes ...

class Announcement(models.Model):
    title = models.CharField(max_length=255, verbose_name="ርዕስ")
    content = models.TextField(verbose_name="ይዘት")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ደራሲ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at'] # Show the newest announcements first
