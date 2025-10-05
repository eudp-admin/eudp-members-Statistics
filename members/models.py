# ===================================================================
#               የተስተካከለው members/models.py
# ===================================================================

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# =========================================================================
# 1. MEMBER MODEL
# =========================================================================
class Member(models.Model):
    # --- Basic Information ---
    full_name = models.CharField(max_length=255, verbose_name="ሙሉ ስም")
    gender = models.CharField(max_length=10, choices=[('Male', 'ወንድ'), ('Female', 'ሴት')], verbose_name="ጾታ")
    date_of_birth = models.DateField(verbose_name="የትውልድ ቀን")
    photo = models.ImageField(upload_to='member_photos/', null=True, blank=True, verbose_name="ፎቶግራፍ")

    # --- Contact Information ---
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="ስልክ ቁጥር")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="ኢሜይል")
    
    REGION_CHOICES = [
        ('አዲስ አበባ', 'አዲስ አበባ'),
        ('አማራ', 'አማራ'),
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
    address_region = models.CharField(max_length=100, verbose_name="ክልል", choices=REGION_CHOICES)
    address_zone = models.CharField(max_length=100, verbose_name="ዞን")
    address_woreda = models.CharField(max_length=100, verbose_name="ወረዳ")
    address_kebele = models.CharField(max_length=100, verbose_name="ቀበሌ")
    
    # --- Party Information ---
    membership_id = models.CharField(max_length=100, unique=True, blank=True, verbose_name="የአባልነት መለያ ቁጥር")
    membership_level = models.CharField(max_length=50, choices=[('Full', 'ሙሉ አባል'), ('Supporter', 'ደጋፊ')], verbose_name="የአባልነት ደረጃ")
    party_role = models.CharField(max_length=100, blank=True, null=True, verbose_name="በፓርቲ ውስጥ ያለ ኃላፊነት")
    join_date = models.DateField(auto_now_add=True, verbose_name="የተቀላቀለበት ቀን")
    is_coordinator = models.BooleanField(default=False, verbose_name="አስተባባሪ ነው?")
    coordinator_region = models.CharField(max_length=100, blank=True, null=True, verbose_name="የሚያስተባብረው ክልል")
    
    # --- Other Information ---
    EDUCATION_CHOICES = [
        ('መሰረታዊ ትምህርት', 'መሰረታዊ ትምህርት'),
        ('ሁለተኛ ደረጃ', 'ሁለተኛ ደረጃ'),
        ('ዲፕሎማ', 'ዲፕሎማ'),
        ('ዲግሪ', 'ዲግሪ'),
        ('ማስተርስ', 'ማስተርስ'),
        ('ዶክትሬት (PhD)', 'ዶክትሬት (PhD)'),
        ('ሌላ', 'ሌላ'),
    ]
    education_level = models.CharField(max_length=100, blank=True, null=True, verbose_name="የትምህርት ደረጃ", choices=EDUCATION_CHOICES)
    profession = models.CharField(max_length=100, blank=True, null=True, verbose_name="የስራ መስክ")

    # --- System Fields ---
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="የአባልነት ሁኔታ (Active)")

    def __str__(self):
        return self.full_name

    # =================== THIS IS THE CORRECTED SAVE METHOD ===================
    def save(self, *args, **kwargs):
        # This logic now ONLY handles the membership ID generation for new members
        # The User creation is handled in the view.
        if not self.pk: # Only run when creating a new member
            current_year = datetime.now().year
            # The region is already validated by the form's choices
            region = self.address_region
            region_code_map = {
                'አማራ': 'AMH', 'ኦሮሚያ': 'ORO', 'ትግራይ': 'TIG', 'አዲስ አበባ': 'AA',
                'ድሬዳዋ': 'DD', 'ደቡብ ኢትዮጵያ': 'SOET', 'ደቡብ ምዕራብ ኢትዮጵያ': 'SWET',
                'ሐረር': 'HAR', 'አፋር': 'AFR', 'ሶማሌ': 'SOM', 'ጋምቤላ': 'GAM',
                'ቤኒሻንጉል ጉሙዝ': 'BEN', 'ሲዳማ': 'SID',
            }
            region_code = region_code_map.get(region, 'OTH')
            
            # Find the last member to determine the next sequence number
            last_member = Member.objects.filter(
                address_region=self.address_region, 
                join_date__year=current_year
            ).order_by('pk').last()
            
            new_seq_num = 1
            if last_member and last_member.membership_id:
                try:
                    last_seq_num = int(last_member.membership_id.split('-')[-1])
                    new_seq_num = last_seq_num + 1
                except (ValueError, IndexError):
                    pass
            
            self.membership_id = f"{region_code}-{current_year}-{new_seq_num:04d}"

        # Call the original save method to save the instance
        super().save(*args, **kwargs)
    # =========================================================================

# =========================================================================
# 2. MEETING, ATTENDANCE, and ANNOUNCEMENT MODELS (No changes needed)
# =========================================================================
class Meeting(models.Model):
    title = models.CharField(max_length=255, verbose_name="የስብሰባው ርዕስ")
    description = models.TextField(blank=True, null=True, verbose_name="አጭር መግለጫ")
    meeting_date = models.DateTimeField(verbose_name="የስብሰባው ቀን እና ሰዓት")
    location = models.CharField(max_length=255, verbose_name="የስብሰባው ቦታ")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ፈጣሪ")
    attendees = models.ManyToManyField(Member, through='Attendance', related_name='attended_meetings', verbose_name="ተሰብሳቢዎች")
    def __str__(self):
        return self.title

class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="አባል")
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name="ስብሰባ")
    attended_at = models.DateTimeField(auto_now_add=True, verbose_name="የተገኘበት ሰዓት")
    class Meta:
        unique_together = ('member', 'meeting')
    def __str__(self):
        return f"{self.member.full_name} attended {self.meeting.title}"

class Announcement(models.Model):
    title = models.CharField(max_length=255, verbose_name="ርዕስ")
    content = models.TextField(verbose_name="ይዘት")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ደራሲ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title
