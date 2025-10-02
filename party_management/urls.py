"""
URL configuration for party_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include  # 'include' እዚህ ላይ መኖሩን አረጋግጥ
from members import views as member_views # አዲስ import
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', member_views.landing_page, name='landing_page'), # የመነሻ ገጽ
    path('app/', include('members.urls')), # የኛ መተግበሪያ ከ /app/ ጀምሮ
    path('accounts/', include('django.contrib.auth.urls')),
]
if settings.DEBUG is False: # Check if we are in production
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
