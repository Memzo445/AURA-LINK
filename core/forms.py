from datetime import date, datetime, timedelta

from django import forms
from django.utils import timezone

DEFAULT_TIME_SLOTS = [
    ('10:00', '10:00'),
    ('12:00', '12:00'),
    ('14:00', '14:00'),
    ('16:00', '16:00'),
    ('18:00', '18:00'),
    ('20:00', '20:00'),
]

WORKING_HOURS_CHOICES = [
    ('', 'Выбрать...'),
    ('Пн–Пт · 10:00–18:00', 'Пн–Пт · 10:00–18:00'),
    ('Пн–Сб · 10:00–20:00', 'Пн–Сб · 10:00–20:00'),
    ('Ежедневно · 11:00–21:00', 'Ежедневно · 11:00–21:00'),
    ('Только по записи', 'Только по записи'),
    ('custom', 'Другое...'),
]

BOOKING_MODE_CHOICES = [
    ('slots', 'Готовые слоты'),
    ('request', 'По записи'),
]

SLOT_STEP_CHOICES = [
    (15, '15 минут'),
    (20, '20 минут'),
    (30, '30 минут'),
    (45, '45 минут'),
    (60, '60 минут'),
    (90, '90 минут'),
    (120, '120 минут'),
]

SERVICE_DURATION_CHOICES = [
    ('', 'Выбрать...'),
    (30, '30 минут'),
    (45, '45 минут'),
    (60, '60 минут'),
    (90, '90 минут'),
    (120, '120 минут'),
]

SERVICE_ICON_CHOICES = [
    ('', 'Выбрать...'),
    ('✂', '✂ Стрижка'),
    ('💈', '💈 Барбер'),
    ('💅', '💅 Ногти'),
    ('👁', '👁 Ресницы'),
    ('🌸', '🌸 Брови'),
    ('🖋', '🖋 Тату'),
    ('✨', '✨ Beauty'),
]


def _normalize_time_value(value):
    if hasattr(value, 'strftime'):
        return value.strftime('%H:%M')
    value = (value or '').strip()
    if not value:
        return ''
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt).strftime('%H:%M')
        except ValueError:
            continue
    return value


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'alex_smith',
            'autocomplete': 'username',
            'class': 'aura-input',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'class': 'aura-input',
        }),
    )


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'alex_smith',
            'autocomplete': 'username',
            'class': 'aura-input',
        }),
    )
    display_name = forms.CharField(
        label='Имя мастера',
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': 'Алекс Смит',
            'class': 'aura-input',
        }),
    )
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'mail@example.com',
            'autocomplete': 'email',
            'class': 'aura-input',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Придумай пароль',
            'autocomplete': 'new-password',
            'class': 'aura-input',
        }),
    )


class ProfileForm(forms.Form):
    display_name = forms.CharField(
        label='Имя мастера',
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': 'Алекс Смит',
            'class': 'aura-input',
        }),
    )
    avatar_file = forms.FileField(
        label='Аватар',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'aura-input aura-file',
            'accept': 'image/*',
        }),
    )


class ServiceForm(forms.Form):
    title = forms.CharField(
        label='Название услуги',
        max_length=160,
        widget=forms.TextInput(attrs={
            'placeholder': 'Мужская стрижка',
            'class': 'aura-input',
        }),
    )
    price = forms.IntegerField(
        label='Цена',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': '5000',
            'min': '0',
            'class': 'aura-input',
            'inputmode': 'numeric',
        }),
    )
    duration_minutes = forms.ChoiceField(
        label='Длительность',
        choices=SERVICE_DURATION_CHOICES,
        widget=forms.Select(attrs={'class': 'aura-input'}),
    )
    icon = forms.ChoiceField(
        label='Иконка',
        choices=SERVICE_ICON_CHOICES,
        widget=forms.Select(attrs={'class': 'aura-input'}),
    )


class ServiceDetailsForm(forms.Form):
    location = forms.CharField(
        label='Адрес',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'с. Талапкер, Целиноградский район, Акмолинская область',
            'class': 'aura-input',
        }),
    )
    location_link = forms.URLField(
        label='Ссылка 2ГИС',
        required=False,
        widget=forms.URLInput(attrs={
            'placeholder': 'https://2gis.kz/...',
            'class': 'aura-input',
        }),
    )
    working_hours = forms.ChoiceField(
        label='Время работы',
        choices=WORKING_HOURS_CHOICES,
        widget=forms.Select(attrs={'class': 'aura-input js-switcher', 'data-target': 'working_hours_custom'}),
    )
    working_hours_custom = forms.CharField(
        label='Свой график',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Например: Сб–Вс · 12:00–18:00',
            'class': 'aura-input js-custom-field',
            'data-source': 'working_hours',
        }),
    )
    booking_mode = forms.ChoiceField(
        label='Режим записи',
        choices=BOOKING_MODE_CHOICES,
        widget=forms.Select(attrs={'class': 'aura-input'}),
    )
    work_start_time = forms.TimeField(
        label='Начало',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'aura-input',
        }),
    )
    work_end_time = forms.TimeField(
        label='Конец',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'aura-input',
        }),
    )
    slot_step_minutes = forms.ChoiceField(
        label='Шаг слота',
        choices=SLOT_STEP_CHOICES,
        widget=forms.Select(attrs={'class': 'aura-input'}),
    )
    description = forms.CharField(
        label='Короткое описание',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Пара строк о себе и стиле работы.',
            'class': 'aura-input',
        }),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normalize_custom_choice('working_hours', 'working_hours_custom', WORKING_HOURS_CHOICES)

    def _normalize_custom_choice(self, field_name, custom_name, choices):
        field_choices = dict(choices)
        if self.is_bound:
            source = self.data.get(field_name) or ''
            custom_value = self.data.get(custom_name) or ''
            if source and source not in field_choices:
                data = self.data.copy()
                data[field_name] = 'custom'
                data[custom_name] = source
                self.data = data
            elif source == 'custom' and not custom_value:
                return
        else:
            source = self.initial.get(field_name) or ''
            custom_value = self.initial.get(custom_name) or ''
            if source and source not in field_choices:
                self.initial[field_name] = 'custom'
                self.initial[custom_name] = source
            elif source == 'custom' and custom_value:
                self.initial[custom_name] = custom_value

    def clean(self):
        cleaned = super().clean()
        cleaned['location'] = (cleaned.get('location') or '').strip()
        cleaned['location_link'] = (cleaned.get('location_link') or '').strip()
        cleaned['description'] = (cleaned.get('description') or '').strip()
        working_hours = (cleaned.get('working_hours') or '').strip()
        working_hours_custom = (cleaned.get('working_hours_custom') or '').strip()
        if working_hours == 'custom':
            cleaned['working_hours'] = working_hours_custom
        cleaned['working_hours'] = (cleaned.get('working_hours') or '').strip()
        cleaned['booking_mode'] = (cleaned.get('booking_mode') or 'slots').strip()
        cleaned['work_start_time'] = _normalize_time_value(cleaned.get('work_start_time'))
        cleaned['work_end_time'] = _normalize_time_value(cleaned.get('work_end_time'))
        cleaned['slot_step_minutes'] = int(cleaned.get('slot_step_minutes') or 60)

        if cleaned['work_start_time'] and cleaned['work_end_time']:
            start = datetime.strptime(cleaned['work_start_time'], '%H:%M').time()
            end = datetime.strptime(cleaned['work_end_time'], '%H:%M').time()
            if (end.hour, end.minute) <= (start.hour, start.minute):
                raise forms.ValidationError('Время окончания должно быть позже начала.')

        return cleaned


class BookingForm(forms.Form):
    client_name = forms.CharField(
        label='Ваше имя',
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': 'Как к вам обращаться',
            'class': 'aura-input',
            'autocomplete': 'name',
        }),
    )
    client_contact = forms.CharField(
        label='Телефон или Telegram',
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': '@username или +7 ...',
            'class': 'aura-input',
            'autocomplete': 'tel',
        }),
    )
    client_email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'mail@example.com',
            'class': 'aura-input',
            'autocomplete': 'email',
        }),
    )
    booking_date = forms.DateField(
        label='Дата',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'aura-input',
        }),
        initial=date.today,
    )
    time_slot = forms.CharField(
        label='Время',
        widget=forms.HiddenInput(),
    )
    notes = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Например: свяжитесь в Telegram',
            'class': 'aura-input',
        }),
    )

    def __init__(self, *args, slots=None, booking_mode='slots', start_time='11:00', end_time='21:00', step_minutes=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.slots = [self._normalize_slot(slot) for slot in (slots or []) if self._normalize_slot(slot)]
        self.booking_mode = booking_mode or 'slots'
        self.start_time = _normalize_time_value(start_time) or '11:00'
        self.end_time = _normalize_time_value(end_time) or '21:00'
        self.step_minutes = int(step_minutes or 60)

        if self.booking_mode == 'request':
            self.fields['time_slot'].widget = forms.TimeInput(attrs={
                'type': 'time',
                'class': 'aura-input',
                'min': self.start_time,
                'max': self.end_time,
                'step': str(max(self.step_minutes, 1) * 60),
            })
        else:
            self.fields['time_slot'].widget = forms.HiddenInput()

        today = timezone.localdate()
        self.fields['booking_date'].widget.attrs.setdefault('min', today.isoformat())
        self.fields['booking_date'].widget.attrs.setdefault('max', (today + timedelta(days=7)).isoformat())

    def _normalize_slot(self, value):
        return _normalize_time_value(value)

    def clean_time_slot(self):
        value = self.cleaned_data.get('time_slot') or ''
        value = self._normalize_slot(value)
        if not value:
            raise forms.ValidationError('Выбери время.')
        if self.slots and value not in self.slots:
            raise forms.ValidationError('Это время уже занято или недоступно.')
        return value

