from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


BOOKING_MODE_CHOICES = [
    ('slots', 'Готовые слоты'),
    ('request', 'По записи'),
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    location = models.CharField(max_length=255, blank=True, default='')
    location_link = models.URLField(blank=True, default='')
    working_hours = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    avatar_file = models.FileField(upload_to='avatars/', blank=True)
    booking_mode = models.CharField(max_length=16, choices=BOOKING_MODE_CHOICES, default='slots')
    work_start_time = models.CharField(max_length=5, blank=True, default='11:00')
    work_end_time = models.CharField(max_length=5, blank=True, default='21:00')
    slot_step_minutes = models.PositiveSmallIntegerField(default=60)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.display_name or self.user.username) or self.user.username
            candidate = base
            i = 1
            while Profile.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                i += 1
                candidate = f"{base}-{i}"
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def avatar_src(self):
        if self.avatar_file:
            try:
                return self.avatar_file.url
            except Exception:
                pass
        return self.avatar_url

    def __str__(self):
        return self.display_name or self.user.username


class Service(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=160)
    price = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(default=60)
    icon = models.CharField(max_length=48, blank=True, default='✦')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class Booking(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DECLINED = 'declined'
    STATUS_DONE = 'done'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Новая'),
        (STATUS_CONFIRMED, 'Принята'),
        (STATUS_DECLINED, 'Отклонена'),
        (STATUS_DONE, 'Завершена'),
        (STATUS_EXPIRED, 'Истекла'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    client_name = models.CharField(max_length=120)
    client_contact = models.CharField(max_length=120)
    client_email = models.EmailField(blank=True, default='')
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=10)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    decline_reason = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.client_name} — {self.booking_date} {self.time_slot}'
