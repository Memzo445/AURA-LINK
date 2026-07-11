from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .forms import (
    LoginForm,
    RegisterForm,
    ProfileForm,
    ServiceForm,
    ServiceDetailsForm,
    BookingForm,
    DEFAULT_TIME_SLOTS,
    WORKING_HOURS_CHOICES,
)
from .models import Profile, Service, Booking
from .utils import available_time_slots, expire_stale_bookings, booking_date_bounds, is_bookable_date
from .email_utils import send_booking_email


def _ensure_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'display_name': user.username, 'slug': user.username},
    )
    return profile


def _first_service(profile):
    return profile.services.order_by('order', 'id').first()


def _occupied_slots(profile, booking_date):
    taken = (
        Booking.objects.filter(
            profile=profile,
            booking_date=booking_date,
            status__in=[Booking.STATUS_ACTIVE, Booking.STATUS_CONFIRMED],
        )
        .values_list('time_slot', flat=True)
    )
    return set(taken)


def _available_slots(profile, booking_date):
    occupied = _occupied_slots(profile, booking_date)
    return available_time_slots(
        DEFAULT_TIME_SLOTS,
        occupied,
        booking_date=booking_date,
        allow_future_dates=True,
        working_hours=profile.working_hours,
        work_start_time=profile.work_start_time,
        work_end_time=profile.work_end_time,
        slot_step_minutes=profile.slot_step_minutes,
    )


def _profile_initial(profile):
    return {
        'display_name': profile.display_name,
    }


def _service_initial(service):
    return {
        'title': service.title if service else '',
        'price': service.price if service else '',
        'duration_minutes': service.duration_minutes if service else 60,
        'icon': service.icon if service else '✂',
    }


def _service_details_initial(profile):
    return {
        'location': profile.location,
        'location_link': profile.location_link,
        'working_hours': profile.working_hours,
        'working_hours_custom': '' if profile.working_hours in dict(WORKING_HOURS_CHOICES) else profile.working_hours,
        'booking_mode': profile.booking_mode or 'slots',
        'work_start_time': profile.work_start_time or '11:00',
        'work_end_time': profile.work_end_time or '21:00',
        'slot_step_minutes': profile.slot_step_minutes or 60,
        'description': profile.description,
    }


def _setup_progress(profile, service):
    step_profile = bool(profile.display_name)
    step_avatar = bool(profile.avatar_src)
    step_service = bool(service and profile.location and profile.working_hours and profile.work_start_time and profile.work_end_time)
    steps = [
        {
            'num': 1,
            'title': 'Заполни профиль',
            'done': step_profile and step_avatar,
            'hint': 'Имя и аватар.',
        },
        {
            'num': 2,
            'title': 'Сохрани услугу',
            'done': step_service,
            'hint': 'Название, цена, график и шаг записи.',
        },
        {
            'num': 3,
            'title': 'Поделись ссылкой',
            'done': step_service,
            'hint': f'aura.link/{profile.slug}',
        },
    ]
    done_count = sum(1 for item in steps if item['done'])
    return steps, done_count


def _dashboard_context(profile, section, request=None, profile_form=None, service_form=None, service_details_form=None):
    expire_stale_bookings(profile)
    service = _first_service(profile)
    bookings = profile.bookings.select_related('service').all()
    counts = {
        'active': bookings.filter(status=Booking.STATUS_ACTIVE).count(),
        'confirmed': bookings.filter(status=Booking.STATUS_CONFIRMED).count(),
        'declined': bookings.filter(status=Booking.STATUS_DECLINED).count(),
        'done': bookings.filter(status=Booking.STATUS_DONE).count(),
        'expired': bookings.filter(status=Booking.STATUS_EXPIRED).count(),
    }
    steps, done_count = _setup_progress(profile, service)
    next_hint = {
        'profile': 'После профиля перейди к услуге.',
        'service': 'После услуги можно просто отправить ссылку клиентам.',
        'bookings': 'Заявки будут появляться после отправки ссылки.',
    }[section]
    next_cta = {
        'profile': {'label': 'Перейти к услуге', 'url': '/dashboard/service/'},
        'service': {'label': 'Открыть записи', 'url': '/dashboard/bookings/'},
        'bookings': {'label': 'Открыть клиентскую ссылку', 'url': f'/u/{profile.slug}/'},
    }[section]
    public_client_url = request.build_absolute_uri(f'/u/{profile.slug}/') if request else f'/u/{profile.slug}/'
    return {
        'profile': profile,
        'service': service,
        'bookings': bookings,
        'counts': counts,
        'section': section,
        'nav_active': section,
        'profile_form': profile_form or ProfileForm(initial=_profile_initial(profile)),
        'service_form': service_form or ServiceForm(initial=_service_initial(service)),
        'service_details_form': service_details_form or ServiceDetailsForm(initial=_service_details_initial(profile)),
        'screen_title': {
            'profile': 'Профиль мастера',
            'service': 'Одна услуга',
            'bookings': 'Записи клиентов',
        }[section],
        'screen_note': {
            'profile': 'Сначала заполни страницу мастера — потом отправляй ссылку клиентам.',
            'service': 'Добавь главную услугу и сделай страницу понятной с первого взгляда.',
            'bookings': 'Все заявки здесь. Принять, отклонить или завершить можно в один тап.',
        }[section],
        'setup_steps': steps,
        'setup_done_count': done_count,
        'setup_total_count': len(steps),
        'next_hint': next_hint,
        'next_cta': next_cta,
        'public_client_url': public_client_url,
    }


def home_redirect(request):
    return redirect('dashboard-profile' if request.user.is_authenticated else 'login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard-profile')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is None:
            messages.error(request, 'Неверный логин или пароль.')
        else:
            login(request, user)
            _ensure_profile(user)
            return redirect('/dashboard/profile/#profile-form')
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard-profile')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from django.contrib.auth.models import User

        username = form.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Такой логин уже занят.')
        else:
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            user.first_name = form.cleaned_data['display_name']
            user.save(update_fields=['first_name'])
            Profile.objects.create(
                user=user,
                display_name=form.cleaned_data['display_name'],
                slug=username,
                location='',
                location_link='',
            )
            login(request, user)
            messages.success(request, 'Профиль создан. Начни с вкладки "Профиль".')
            return redirect('dashboard-profile')
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_redirect(request):
    return redirect('dashboard-profile')


@login_required
def dashboard_profile_view(request):
    profile = _ensure_profile(request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, initial=_profile_initial(profile))
        if form.is_valid():
            profile.display_name = form.cleaned_data['display_name']
            if form.cleaned_data.get('avatar_file'):
                profile.avatar_file = form.cleaned_data['avatar_file']
            profile.save()
            messages.success(request, 'Профиль сохранён. Теперь добавь услугу.')
            return redirect('dashboard-profile')
        messages.error(request, 'Проверь поля профиля.')
        return render(request, 'dashboard.html', _dashboard_context(profile, 'profile', request=request, profile_form=form))
    return render(request, 'dashboard.html', _dashboard_context(profile, 'profile', request=request))


@login_required
def dashboard_service_view(request):
    profile = _ensure_profile(request.user)
    if request.method == 'POST':
        service_form = ServiceForm(request.POST)
        service_details_form = ServiceDetailsForm(request.POST)
        if service_form.is_valid() and service_details_form.is_valid():
            service = _first_service(profile)
            if service is None:
                service = Service(profile=profile, order=1)
            service.title = service_form.cleaned_data['title']
            service.price = service_form.cleaned_data['price']
            service.duration_minutes = int(service_form.cleaned_data['duration_minutes'])
            service.icon = service_form.cleaned_data['icon']
            service.order = 1
            service.save()

            profile.location = service_details_form.cleaned_data['location']
            profile.location_link = service_details_form.cleaned_data['location_link']
            profile.working_hours = service_details_form.cleaned_data['working_hours']
            profile.booking_mode = service_details_form.cleaned_data['booking_mode']
            profile.work_start_time = service_details_form.cleaned_data['work_start_time']
            profile.work_end_time = service_details_form.cleaned_data['work_end_time']
            profile.slot_step_minutes = service_details_form.cleaned_data['slot_step_minutes']
            profile.description = service_details_form.cleaned_data['description']
            profile.save(update_fields=[
                'location',
                'location_link',
                'working_hours',
                'booking_mode',
                'work_start_time',
                'work_end_time',
                'slot_step_minutes',
                'description',
            ])

            messages.success(request, 'Услуга и данные для клиента сохранены.')
            return redirect('/dashboard/service/#service-form')
        messages.error(request, 'Проверь поля услуги и данные клиента.')
        return render(
            request,
            'dashboard.html',
            _dashboard_context(
                profile,
                'service',
                request=request,
                service_form=service_form,
                service_details_form=service_details_form,
            ),
        )
    return render(request, 'dashboard.html', _dashboard_context(profile, 'service', request=request))


@login_required
def dashboard_bookings_view(request):
    profile = _ensure_profile(request.user)
    expire_stale_bookings(profile)
    return render(request, 'dashboard.html', _dashboard_context(profile, 'bookings', request=request))


@login_required
@require_POST
def booking_update_status(request, pk):
    profile = _ensure_profile(request.user)
    expire_stale_bookings(profile)
    booking = get_object_or_404(Booking, pk=pk, profile=profile)
    status = request.POST.get('status')
    decline_reason_choice = (request.POST.get('decline_reason_choice') or '').strip()
    decline_reason_custom = (request.POST.get('decline_reason_custom') or '').strip()

    if status in dict(Booking.STATUS_CHOICES):
        booking.status = status
        email_subject = None
        email_message = None

        if status == Booking.STATUS_DECLINED:
            reason = decline_reason_choice
            if reason == 'Другое':
                reason = decline_reason_custom
            elif decline_reason_custom and not reason:
                reason = decline_reason_custom
            booking.decline_reason = reason or 'Мастер не смог принять заявку.'
            email_subject = 'Ваша заявка отклонена'
            email_message = (
                f'Здравствуйте, {booking.client_name}!\n\n'
                f'Ваша запись на {booking.booking_date} в {booking.time_slot} отклонена.\n'
                f'Причина: {booking.decline_reason}'
            )
        elif status == Booking.STATUS_CONFIRMED:
            booking.decline_reason = ''
            email_subject = 'Ваша заявка принята'
            email_message = (
                f'Здравствуйте, {booking.client_name}!\n\n'
                f'Вы записаны на {booking.booking_date} в {booking.time_slot}.\n'
                f'Мастер скоро свяжется с вами.'
            )
        elif status == Booking.STATUS_DONE:
            booking.decline_reason = booking.decline_reason or ''

        booking.save(update_fields=['status', 'decline_reason'])

        if email_subject and email_message:
            send_booking_email(
                booking.client_email,
                email_subject,
                email_message,
                reply_to=[booking.profile.user.email] if booking.profile.user.email else None,
            )

        messages.success(request, 'Статус записи обновлён.')
    return redirect('/dashboard/bookings/#booking-list')


def client_page(request, slug):

    profile = get_object_or_404(Profile, slug=slug)
    expire_stale_bookings(profile)
    service = _first_service(profile)

    today, max_date = booking_date_bounds()
    selected_date = parse_date(request.GET.get('date') or '') or today
    if not is_bookable_date(selected_date):
        selected_date = today

    available_slots = _available_slots(profile, selected_date)
    booking_form = BookingForm(
        slots=available_slots,
        booking_mode=profile.booking_mode,
        start_time=profile.work_start_time,
        end_time=profile.work_end_time,
        step_minutes=profile.slot_step_minutes,
        initial={'booking_date': selected_date},
    )

    return render(request, 'client.html', {
        'profile': profile,
        'service': service,
        'booking_form': booking_form,
        'selected_date': selected_date.isoformat(),
        'booking_min_date': today.isoformat(),
        'booking_max_date': max_date.isoformat(),
        'available_slots': available_slots,
        'has_slots': bool(available_slots),
        'booking_mode': profile.booking_mode,
        'work_start_time': profile.work_start_time,
        'work_end_time': profile.work_end_time,
        'slot_step_minutes': profile.slot_step_minutes,
    })


def client_booking_create(request, slug):
    profile = get_object_or_404(Profile, slug=slug)
    expire_stale_bookings(profile)
    if request.method != 'POST':
        return redirect('client-page', slug=slug)

    service = _first_service(profile)
    if service is None:
        messages.error(request, 'У мастера пока нет услуги.')
        return redirect('client-page', slug=slug)

    today, max_date = booking_date_bounds()
    booking_date = parse_date(request.POST.get('booking_date') or '') or today
    if not is_bookable_date(booking_date):
        messages.error(request, 'Дата записи недоступна.')
        return redirect(f'/u/{slug}/?date={today.isoformat()}')

    available_slots = _available_slots(profile, booking_date)
    form = BookingForm(
        request.POST,
        slots=available_slots,
        booking_mode=profile.booking_mode,
        start_time=profile.work_start_time,
        end_time=profile.work_end_time,
        step_minutes=profile.slot_step_minutes,
    )

    if not form.is_valid():
        messages.error(request, 'Проверьте данные записи.')
        return redirect(f'/u/{slug}/?date={booking_date.isoformat()}')

    time_slot = form.cleaned_data['time_slot']
    if time_slot not in available_slots:
        messages.error(request, 'Это время уже занято или уже прошло.')
        return redirect(f'/u/{slug}/?date={booking_date.isoformat()}')

    booking = Booking.objects.create(
        profile=profile,
        service=service,
        client_name=form.cleaned_data['client_name'],
        client_contact=form.cleaned_data['client_contact'],
        client_email=form.cleaned_data['client_email'],
        booking_date=booking_date,
        time_slot=time_slot,
        notes=form.cleaned_data['notes'],
        status=Booking.STATUS_ACTIVE,
    )
    send_booking_email(
        booking.client_email,
        'Заявка создана',
        f'Здравствуйте, {booking.client_name}!\n\nВы записаны на {booking.booking_date} в {booking.time_slot}.\nСтатус: новая.',
        reply_to=[booking.profile.user.email] if booking.profile.user.email else None,
    )
    messages.success(request, 'Запись отправлена мастеру. Он увидит её в разделе "Записи".')
    return redirect(f'/u/{slug}/?date={booking_date.isoformat()}')
