from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import DEFAULT_TIME_SLOTS
from .models import Profile, Service, Booking
from .api_serializers import ProfileSerializer, ServiceSerializer, BookingSerializer
from .utils import available_time_slots, expire_stale_bookings, booking_date_bounds, is_bookable_date
from .email_utils import send_booking_email


def _tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


def _first_service(profile):
    return profile.services.order_by('order', 'id').first()


def _available_slots(profile, booking_date):
    taken = set(
        Booking.objects.filter(
            profile=profile,
            booking_date=booking_date,
            status__in=[Booking.STATUS_ACTIVE, Booking.STATUS_CONFIRMED],
        ).values_list('time_slot', flat=True)
    )
    return available_time_slots(
        DEFAULT_TIME_SLOTS,
        taken,
        booking_date=booking_date,
        allow_future_dates=True,
        working_hours=profile.working_hours,
        work_start_time=profile.work_start_time,
        work_end_time=profile.work_end_time,
        slot_step_minutes=profile.slot_step_minutes,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def token_login(request):
    user = authenticate(username=request.data.get('username', ''), password=request.data.get('password', ''))
    if not user:
        return Response({'detail': 'Неверный логин или пароль.'}, status=400)
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'display_name': user.username, 'slug': user.username},
    )
    return Response({'tokens': _tokens(user), 'profile': ProfileSerializer(profile).data})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = (request.data.get('username') or '').strip()
    display_name = (request.data.get('display_name') or '').strip() or username
    email = (request.data.get('email') or '').strip()
    password = request.data.get('password') or ''
    if not username or not password:
        return Response({'detail': 'Нужны логин и пароль.'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'detail': 'Такой логин уже занят.'}, status=400)
    user = User.objects.create_user(username=username, email=email, password=password)
    profile = Profile.objects.create(user=user, display_name=display_name, slug=username)
    return Response({'tokens': _tokens(user), 'profile': ProfileSerializer(profile).data}, status=201)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def me(request):
    profile = request.user.profile
    expire_stale_bookings(profile)
    if request.method == 'GET':
        return Response(ProfileSerializer(profile).data)
    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def services(request):
    profile = request.user.profile
    expire_stale_bookings(profile)
    if request.method == 'GET':
        service = _first_service(profile)
        if not service:
            return Response([])
        return Response([ServiceSerializer(service).data])

    existing = _first_service(profile)
    service = existing or Service(profile=profile, order=1)
    serializer = ServiceSerializer(service, data=request.data, partial=bool(existing))
    serializer.is_valid(raise_exception=True)
    instance = serializer.save(profile=profile, order=1)
    return Response(ServiceSerializer(instance).data, status=201 if existing is None else 200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bookings(request):
    profile = request.user.profile
    expire_stale_bookings(profile)
    qs = profile.bookings.select_related('service').all()
    status_filter = request.query_params.get('status')
    if status_filter in dict(Booking.STATUS_CHOICES):
        qs = qs.filter(status=status_filter)
    return Response(BookingSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_profile(request, slug):
    profile = get_object_or_404(Profile, slug=slug)
    expire_stale_bookings(profile)
    service = _first_service(profile)
    today = timezone.localdate()
    selected_date = parse_date(request.query_params.get('date') or '') or today
    if not is_bookable_date(selected_date):
        selected_date = today
    return Response({
        'profile': ProfileSerializer(profile).data,
        'service': ServiceSerializer(service).data if service else None,
        'available_slots': _available_slots(profile, selected_date),
        'bookings': BookingSerializer(profile.bookings.filter(status__in=['active', 'confirmed']), many=True).data,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def public_book(request, slug):
    profile = get_object_or_404(Profile, slug=slug)
    expire_stale_bookings(profile)
    service = _first_service(profile)
    if not service:
        return Response({'detail': 'У мастера пока нет услуги.'}, status=400)

    booking_date = parse_date(request.data.get('booking_date') or '')
    today, max_date = booking_date_bounds()
    if booking_date is None:
        return Response({'detail': 'Нужно выбрать дату.'}, status=400)
    if not is_bookable_date(booking_date):
        return Response({'detail': 'Дата записи недоступна.'}, status=400)

    time_slot = request.data.get('time_slot')
    if time_slot not in _available_slots(profile, booking_date):
        return Response({'detail': 'Это время уже занято или уже прошло.'}, status=400)

    client_name = (request.data.get('client_name') or '').strip()
    client_contact = (request.data.get('client_contact') or '').strip()
    client_email = (request.data.get('client_email') or '').strip()
    if not client_name or not client_contact or not client_email:
        return Response({'detail': 'Нужно указать имя, контакт и email.'}, status=400)

    booking = Booking.objects.create(
        profile=profile,
        service=service,
        client_name=client_name,
        client_contact=client_contact,
        client_email=client_email,
        booking_date=booking_date,
        time_slot=time_slot,
        notes=(request.data.get('notes') or '').strip(),
        status=Booking.STATUS_ACTIVE,
    )
    send_booking_email(
        booking.client_email,
        'Заявка создана',
        f'Здравствуйте, {booking.client_name}!\n\nВы записаны на {booking.booking_date} в {booking.time_slot}.\nСтатус: новая.',
        reply_to=[booking.profile.user.email] if booking.profile.user.email else None,
    )
    return Response(BookingSerializer(booking).data, status=201)
