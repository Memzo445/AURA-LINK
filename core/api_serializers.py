from rest_framework import serializers
from .models import Profile, Service, Booking


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'username',
            'display_name',
            'slug',
            'location',
            'location_link',
            'working_hours',
            'description',
            'avatar_url',
            'avatar_file',
            'booking_mode',
            'work_start_time',
            'work_end_time',
            'slot_step_minutes',
        ]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'title', 'price', 'duration_minutes', 'icon', 'order']


class BookingSerializer(serializers.ModelSerializer):
    service_title = serializers.CharField(source='service.title', read_only=True)
    service_price = serializers.IntegerField(source='service.price', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'service',
            'service_title',
            'service_price',
            'client_name',
            'client_contact',
            'client_email',
            'booking_date',
            'time_slot',
            'status',
            'decline_reason',
            'notes',
            'created_at',
        ]
