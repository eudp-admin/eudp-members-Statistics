# ===================================================================
#               Corrected and Cleaned members/views.py
# ===================================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.http import HttpResponse
import json
import csv
from datetime import datetime

# Import models and forms
from .models import Member, Announcement
from .forms import MemberCreationForm, MemberUpdateForm

# ------------------ Permission Check Function ------------------
def is_staff_member(user):
    return user.is_staff

# ------------------ Views ------------------

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('login_redirect')
    return render(request, 'members/landing_page.html')

def register_member(request):
    if request.method == 'POST':
        form = MemberCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Member'ኡን ፍጠር ነገር ግን ዳታቤዝ ላይ አታስቀምጠው
            new_member = form.save(commit=False)
            
            username = new_member.phone_number
            password = "password123"

            # 2. የተጠቃሚ ስሙ (ስልክ ቁጥሩ) ከዚህ በፊት መኖሩን አረጋግጥ
            if User.objects.filter(username=username).exists():
                messages.error(request, f"በዚህ ስልክ ቁጥር ({username}) የተመዘገበ ተጠቃሚ ከዚህ በፊት አለ።")
                return render(request, 'members/register_form.html', {'form': form})

            try:
                # 3. አዲሱን User አካውንት ፍጠር
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=new_member.email if new_member.email else ""
                )
                
                # 4. አዲሱን User ከ Member'ኡ ጋር አገናኘው
                new_member.user = user
                
                # 5. አሁን Member'ኡን ከነግንኙነቱ ዳታቤዝ ላይ አስቀምጠው
                new_member.save()

                print(f"SUCCESS: Directly created and linked user '{username}' in the view.")

                # 6. የመግቢያ መረጃውን ለስኬት ገጹ አሳልፍ
                request.session['new_username'] = username
                request.session['new_password'] = password
                
                return redirect('registration_success')

            except Exception as e:
                # የሆነ ችግር ከተፈጠረ፣ ለተጠቃሚው አሳውቅ
                print(f"CRITICAL ERROR during user creation in view: {e}")
                messages.error(request, "ምዝገባው ላይ ያልተጠበቀ ስህተት አጋጥሟል። እባክዎ እንደገና ይሞክሩ።")

    else: # request.method is GET
        form = MemberCreationForm()
        
    context = {
        'form': form,
        'page_title': 'አዲስ አባል መመዝገቢያ'
    }
    return render(request, 'members/register_form.html', context)
def registration_success(request):
    new_username = request.session.get('new_username', 'የለም')
    new_password = request.session.get('new_password', 'የለም')
    if 'new_username' in request.session:
        del request.session['new_username']
    if 'new_password' in request.session:
        del request.session['new_password']
    context = {'new_username': new_username, 'new_password': new_password}
    return render(request, 'members/registration_success.html', context)

@login_required
def login_redirect_view(request):
    user = request.user
    if user.is_staff:
        return redirect('dashboard')
    else:
        return redirect('profile')

@login_required
def profile(request):
    member_profile = get_object_or_404(Member, user=request.user)
    context = {'member': member_profile}
    return render(request, 'members/profile.html', context)

@login_required
def profile_update(request):
    member_profile = get_object_or_404(Member, user=request.user)
    if request.method == 'POST':
        form = MemberUpdateForm(request.POST, request.FILES, instance=member_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'የግል መረጃዎ በተሳካ ሁኔታ ተስተካክሏል።')
            return redirect('profile')
    else:
        form = MemberUpdateForm(instance=member_profile)
    context = {'form': form, 'page_title': 'የግል መረጃ ማስተካከያ'}
    return render(request, 'members/profile_update_form.html', context)

@login_required
def announcement_list(request):
    announcements = Announcement.objects.all()
    context = {'announcements': announcements, 'page_title': 'ማስታወቂያዎች እና ዜናዎች'}
    return render(request, 'members/announcement_list.html', context)

@user_passes_test(is_staff_member)
def dashboard(request):
    user = request.user
    base_queryset = Member.objects.filter(is_active=True)
    if not user.is_superuser and user.groups.filter(name='የክልል አስተባባሪ').exists():
        try:
            coordinator_profile = Member.objects.get(user=user, is_coordinator=True)
            if coordinator_profile.coordinator_region:
                base_queryset = base_queryset.filter(address_region=coordinator_profile.coordinator_region)
        except Member.DoesNotExist:
            base_queryset = Member.objects.none()
            
    total_members = base_queryset.count()
    gender_distribution = base_queryset.values('gender').annotate(count=Count('gender'))
    members_by_region = base_queryset.values('address_region').annotate(count=Count('address_region')).order_by('-count')
    recent_members = base_queryset.order_by('-join_date')[:5]
    members_by_year_data = base_queryset.annotate(year=ExtractYear('join_date')).values('year').annotate(count=Count('id')).order_by('year')
    bar_chart_labels = [str(item['year']) for item in members_by_year_data]
    bar_chart_data = [item['count'] for item in members_by_year_data]
    pie_chart_labels = ["ወንድ" if item['gender'] == 'Male' else "ሴት" for item in gender_distribution]
    pie_chart_data = [item['count'] for item in gender_distribution]
    context = {
        'page_title': 'የአስተዳደር ዳሽቦርድ',
        'total_members': total_members,
        'gender_distribution': gender_distribution,
        'members_by_region': members_by_region,
        'recent_members': recent_members,
        'bar_chart_labels': json.dumps(bar_chart_labels),
        'bar_chart_data': json.dumps(bar_chart_data),
        'pie_chart_labels': json.dumps(pie_chart_labels),
        'pie_chart_data': json.dumps(pie_chart_data),
    }
    return render(request, 'members/dashboard.html', context)

@user_passes_test(is_staff_member)
def member_list(request):
    user = request.user
    base_queryset = Member.objects.filter(is_active=True).order_by('full_name')
    if not user.is_superuser and user.groups.filter(name='የክልል አስተባባሪ').exists():
        try:
            coordinator_profile = Member.objects.get(user=user, is_coordinator=True)
            if coordinator_profile.coordinator_region:
                base_queryset = base_queryset.filter(address_region=coordinator_profile.coordinator_region)
        except Member.DoesNotExist:
            base_queryset = Member.objects.none()
    query = request.GET.get('query')
    region = request.GET.get('region')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if query:
        base_queryset = base_queryset.filter(Q(full_name__icontains=query) | Q(membership_id__icontains=query))
    if region:
        base_queryset = base_queryset.filter(address_region__icontains=region)
    if start_date:
        base_queryset = base_queryset.filter(join_date__gte=start_date)
    if end_date:
        base_queryset = base_queryset.filter(join_date__lte=end_date)
    context = {'members': base_queryset, 'page_title': 'የፓርቲው አባላት ዝርዝር'}
    return render(request, 'members/member_list.html', context)
@login_required
def member_id_card(request, pk):
    member = get_object_or_404(Member, pk=pk)
    context = {
        'member': member
    }
    return render(request, 'members/id_card_template.html', context)    
@login_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    context = {'member': member}
    return render(request, 'members/member_detail.html', context)

@user_passes_test(is_staff_member)
def export_members_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="members_report.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['ሙሉ ስም', 'የአባልነት መለያ', 'ስልክ ቁጥር', 'ጾታ', 'ክልል', 'የተቀላቀለበት ቀን'])
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
    for member in queryset:
        writer.writerow([member.full_name, member.membership_id, member.phone_number, member.get_gender_display(), member.address_region, member.join_date])
    return response
    
