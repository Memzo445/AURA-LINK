from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from core import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/profile/', views.dashboard_profile_view, name='dashboard-profile'),
    path('dashboard/service/', views.dashboard_service_view, name='dashboard-service'),
    path('dashboard/bookings/', views.dashboard_bookings_view, name='dashboard-bookings'),
    path('dashboard/bookings/<int:pk>/status/', views.booking_update_status, name='booking-status'),

    path('u/<slug:slug>/', views.client_page, name='client-page'),
    path('u/<slug:slug>/book/', views.client_booking_create, name='client-booking-create'),

    path('api/', include('core.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
