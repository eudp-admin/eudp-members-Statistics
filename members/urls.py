from django.urls import path
from . import views
urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('register/', views.register_member, name='register_member'), # ይህንን አዲስ መስመር ጨምር
    path('<int:pk>/', views.member_detail, name='member_detail'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_update, name='profile_update'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/csv/', views.export_members_csv, name='export_members_csv'),
    path('login_redirect/', views.login_redirect_view, name='login_redirect'),
    path('announcements/', views.announcement_list, name='announcements'),
    path('register/success/', views.registration_success, name='registration_success'),
]
