from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    path('token/', api_views.token_login, name='api-token-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('register/', api_views.register, name='api-register'),
    path('me/', api_views.me, name='api-me'),
    path('services/', api_views.services, name='api-services'),
    path('bookings/', api_views.bookings, name='api-bookings'),
    path('public/<slug:slug>/', api_views.public_profile, name='api-public-profile'),
    path('public/<slug:slug>/book/', api_views.public_book, name='api-public-book'),
]
