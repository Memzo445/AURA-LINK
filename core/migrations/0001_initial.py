# Minimal migration file included for completeness.
# The provided SQLite database is already prepared for local demo use.
from django.db import migrations, models
import django.db.models.deletion
import django.utils.text
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(max_length=120)),
                ('slug', models.SlugField(max_length=140, unique=True)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('working_hours', models.CharField(blank=True, max_length=120)),
                ('description', models.TextField(blank=True)),
                ('avatar_url', models.URLField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('price', models.PositiveIntegerField()),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('icon', models.CharField(blank=True, default='✦', max_length=48)),
                ('order', models.PositiveIntegerField(default=0)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='core.profile')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_name', models.CharField(max_length=120)),
                ('client_contact', models.CharField(max_length=120)),
                ('booking_date', models.DateField()),
                ('time_slot', models.CharField(max_length=10)),
                ('status', models.CharField(choices=[('active', 'Новая'), ('confirmed', 'Принята'), ('declined', 'Отклонена'), ('done', 'Завершена'), ('expired', 'Истекла')], default='active', max_length=16)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='core.profile')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.service')),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]
