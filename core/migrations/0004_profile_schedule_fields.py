from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_profile_location_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='booking_mode',
            field=models.CharField(choices=[('slots', 'Готовые слоты'), ('request', 'По записи')], default='slots', max_length=16),
        ),
        migrations.AddField(
            model_name='profile',
            name='work_start_time',
            field=models.CharField(blank=True, default='11:00', max_length=5),
        ),
        migrations.AddField(
            model_name='profile',
            name='work_end_time',
            field=models.CharField(blank=True, default='21:00', max_length=5),
        ),
        migrations.AddField(
            model_name='profile',
            name='slot_step_minutes',
            field=models.PositiveSmallIntegerField(default=60),
        ),
    ]
