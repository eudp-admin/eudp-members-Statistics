from django.shortcuts import render, get_object_or_404, redirect
from .models import Member
from .forms import MemberCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import MemberCreationForm, MemberUpdateForm
from django.db.models import Count
from django.db.models.functions import ExtractYear
import json
from django.db.models import Q
import csv
from django.http import HttpResponse
from datetime import datetime
from .models import Announcement # Announcement'ን import አድርግ


# ------------------ የፍቃድ ማረጋገጫ ተግባር (Permission Check Function) ------------------
def is_staff_member(user):
    """ይህ ተግባር ተጠቃሚው 'staff' መሆኑን ወይም አለመሆኑን ያረጋግጣል"""
    return user.is_staff

# ------------------ ዋና ዋና ተግባራት (Views) ------------------

# ይህ ተግባር አሁን በ staff አባላት ብቻ ነው የሚታየው
@user_passes_test(is_staff_member)
def member_list(request):
    """ሁሉንም አባላት በዝርዝር ያሳያል (ለአስተዳዳሪዎች ብቻ)"""
    # Use the same filtering base as the dashboard for consistency
    base_queryset = Member.objects.filter(is_active=True).order_by('full_name')

    # Regional filtering (Simplified assumption based on dashboard logic)
    user = request.user
    if not user.is_superuser and user.groups.filter(name='የክልል አስተባባሪ').exists():
        try:
            coordinator_profile = Member.objects.get(user=user, is_coordinator=True)
            if coordinator_profile.coordinator_region:
                base_queryset = base_queryset.filter(address_region=coordinator_profile.coordinator_region)
        except Member.DoesNotExist:
            base_queryset = Member.objects.none()

    active_members = base_queryset
    context = {
        'members': active_members,
        'page_title': 'የፓርቲው አባላት ዝርዝር'
    }
    return render(request, 'members/member_list.html', context)

# ይህ ተግባር ሎግอิน ባደረገ ማንኛውም ሰው ይታያል
@login_required
def member_detail(request, pk):
    """የአንድን አባል ዝርዝር መረጃ ያሳያል"""
    member = get_object_or_404(Member, pk=pk)
    context = {
        'member': member,
    }
    return render(request, 'members/member_detail.html', context)

# ይህ ተግባር ለማንም ሰው (ሎግอิน ሳያደርግም) ክፍት ነው
def register_member(request):
    """አዲስ አባል የሚመዘገብበትን ፎርም ያሳያል"""
    if request.method == 'POST':
        form = MemberCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if a user is logged in to associate the record creator
            if request.user.is_authenticated:
                member = form.save(commit=False)
                # Note: The Member model doesn't have a 'created_by' field,
                # but it might be useful to set a default user if required.
                member.save()
            else:
                 form.save()
            messages.success(request, 'ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል! እናመሰግናለን።')
            return redirect('member_list')
    else:
        form = MemberCreationForm()
        
    context = {
        'form': form,
        'page_title': 'አዲስ አባል መመዝገቢያ',
    }
    return render(request, 'members/register_form.html', context)

# ይህ ተግባር ሎግอิน ባደረገ ሰው ብቻ ነው የሚታየው
@login_required
def profile(request):
    """የገባውን ተጠቃሚ የግል መረጃ ገጽ ያሳያል"""
    # Assuming 'user' is a OneToOneField on the Member model
    member_profile = get_object_or_404(Member, user=request.user)
    context = {
        'member': member_profile
    }
    return render(request, 'members/profile.html', context)

@login_required
def login_redirect_view(request):
    """
    After login, this view checks the user's role and redirects them
    to the appropriate page.
    """
    user = request.user
    if user.is_staff:
        # User is a staff member or superuser, redirect to dashboard
        return redirect('dashboard')
    else:
        # User is a regular member, redirect to their profile page
        return redirect('profile')
    
@login_required
def profile_update(request):
    # Get the profile of the currently logged-in user
    member_profile = get_object_or_404(Member, user=request.user)

    if request.method == 'POST':
        # Populate the form with submitted data and the existing profile instance
        form = MemberUpdateForm(request.POST, request.FILES, instance=member_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'የግል መረጃዎ በተሳካ ሁኔታ ተስተካክሏል።')
            return redirect('profile')
    else:
        # Show the form pre-populated with the user's current data
        form = MemberUpdateForm(instance=member_profile)
        
    context = {
        'form': form,
        'page_title': 'የግል መረጃ ማስተካከያ'
    }
    return render(request, 'members/profile_update_form.html', context)

@user_passes_test(is_staff_member)
def dashboard(request):
    user = request.user
    
    # Start with a base queryset of all active members
    base_queryset = Member.objects.filter(is_active=True)
    
    # If the user is a regional coordinator, filter the queryset by their region
    if not user.is_superuser and user.groups.filter(name='የክልል አስተባባሪ').exists():
        try:
            # Note: 'is_coordinator' and 'coordinator_region' fields must exist on the Member model
            coordinator_profile = Member.objects.get(user=user, is_coordinator=True) 
            if coordinator_profile.coordinator_region:
                base_queryset = base_queryset.filter(address_region=coordinator_profile.coordinator_region)
        except Member.DoesNotExist:
            base_queryset = Member.objects.none()

    # --- የፍለጋ አመክንዮ (Search Logic) ---
    query = request.GET.get('query')
    region = request.GET.get('region')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if query:
        base_queryset = base_queryset.filter(
            Q(full_name__icontains=query) | 
            Q(membership_id__icontains=query)
        )
    
    if region:
        base_queryset = base_queryset.filter(address_region__icontains=region)
    
    if start_date:
        base_queryset = base_queryset.filter(join_date__gte=start_date)
    
    if end_date:
        base_queryset = base_queryset.filter(join_date__lte=end_date)
    
    # --- Calculate Statistics ---
    total_members = base_queryset.count()
    
    gender_distribution = base_queryset.values('gender').annotate(count=Count('gender'))
    
    members_by_region = base_queryset.values('address_region').annotate(count=Count('address_region')).order_by('-count')
    
    recent_members = base_queryset.order_by('-join_date')[:5] # Get the 5 most recent members

    # --- ለግራፍ የሚሆን መረጃ ማዘጋጀት ---
    # 1. ለባር ግራፍ (አባላት በየዓመቱ)
    members_by_year_data = base_queryset.annotate(year=ExtractYear('join_date')) \
                                        .values('year') \
                                        .annotate(count=Count('id')) \
                                        .order_by('year')
    
    bar_chart_labels = [str(item['year']) for item in members_by_year_data]
    bar_chart_data = [item['count'] for item in members_by_year_data]

    # 2. ለፓይ ቻርት (አባላት በጾታ)
    pie_chart_labels = []
    pie_chart_data = []
    for item in gender_distribution:
        pie_chart_labels.append("ወንድ" if item['gender'] == 'Male' else "ሴት")
        pie_chart_data.append(item['count'])
    
    # Only one context dictionary should be returned
    context = {
        'page_title': 'የአስተዳደር ዳሽቦርድ',
        'total_members': total_members,
        'gender_distribution': gender_distribution,
        'members_by_region': members_by_region,
        'recent_members': recent_members,
        
        # Context data for the charts
        'bar_chart_labels': json.dumps(bar_chart_labels),
        'bar_chart_data': json.dumps(bar_chart_data),
        'pie_chart_labels': json.dumps(pie_chart_labels),
        'pie_chart_data': json.dumps(pie_chart_data),
    }
    return render(request, 'members/dashboard.html', context)

@user_passes_test(is_staff_member)
def export_members_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="members_report.csv"'
    response.write(u'\ufeff'.encode('utf8')) # For UTF-8 characters like Amharic

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(['ሙሉ ስም', 'የአባልነት መለያ', 'ስልክ ቁጥር', 'ጾታ', 'ክልል', 'የተቀላቀለበት ቀን'])

    # --- Apply the Filtering Logic ---
    user = request.user
    queryset = Member.objects.filter(is_active=True).order_by('full_name')

    if not user.is_superuser and user.groups.filter(name='የክልል አስተባባሪ').exists():
        try:
            coordinator_profile = Member.objects.get(user=user, is_coordinator=True)
            if coordinator_profile.coordinator_region:
                queryset = queryset.filter(address_region=coordinator_profile.coordinator_region)
        except Member.DoesNotExist:
            queryset = Member.objects.none()

    query = request.GET.get('query')
    region = request.GET.get('region')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if query:
        queryset = queryset.filter(Q(full_name__icontains=query) | Q(membership_id__icontains=query))
    if region:
        queryset = queryset.filter(address_region__icontains=region)
    if start_date:
        queryset = queryset.filter(join_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(join_date__lte=end_date)
        
    # Write the data rows
    for member in queryset:
        writer.writerow([member.full_name, member.membership_id, member.phone_number, member.get_gender_display(), member.address_region, member.join_date])

    # --- THE FIX: Correct the return statement ---
    return response
@login_required
def announcement_list(request):
    announcements = Announcement.objects.all()
    context = {
        'announcements': announcements,
        'page_title': 'ማስታወቂያዎች እና ዜናዎች'
    }
    return render(request, 'members/announcement_list.html', context)
def landing_page(request):
    # If the user is already logged in, redirect them to their dashboard/profile
    if request.user.is_authenticated:
        return redirect('login_redirect')
    
    return render(request, 'members/landing_page.html')