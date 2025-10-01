from django.contrib import admin
# Consolidate imports and remove the undefined 'Payment'
from .models import Member, Meeting, Attendance, Announcement

# ------------------------------------------------------------------------

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('membership_id', 'full_name', 'phone_number', 'address_region', 'is_active')
    search_fields = ('full_name', 'phone_number', 'membership_id')
    list_filter = ('is_active', 'membership_level', 'address_region')
    ordering = ['full_name']
    
    # Making some fields read-only
    readonly_fields = ('membership_id', 'join_date', 'created_at', 'updated_at')

# ------------------------------------------------------------------------

class AttendanceInline(admin.TabularInline):
    # The Attendance model is the 'through' model for the Meeting-Member relationship
    model = Attendance
    extra = 1 # Changed extra from 10 to 1 for better admin UX
    # You might want to make attended_at readonly since it's auto_now_add
    readonly_fields = ('attended_at',) 

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'meeting_date', 'location', 'created_by') # Added created_by to list display
    list_filter = ('meeting_date', 'location')
    search_fields = ('title', 'location')
    # Fields to display in the main form, excluding attendees which are managed by the inline
    fields = ('title', 'description', 'meeting_date', 'location') 
    inlines = [AttendanceInline] # Inline the attendance records
    readonly_fields = ('created_by',) # Ensure created_by is only set automatically

    def save_model(self, request, obj, form, change):
        # Automatically set the creator of the meeting ONLY on creation (if pk is None)
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# ------------------------------------------------------------------------

# FIX: Moved AnnouncementAdmin definition to the correct top level
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author')
    # Ensure 'author' is set automatically and cannot be changed manually
    readonly_fields = ('author', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        # Automatically set the author to the current logged-in user
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)