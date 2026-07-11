# Generated manually for email notifications
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_profile_schedule_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='client_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='booking',
            name='decline_reason',
            field=models.TextField(blank=True, default=''),
        ),
    ]
