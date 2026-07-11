from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_profile_avatar_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='location_link',
            field=models.URLField(blank=True, default=''),
        ),
    ]
