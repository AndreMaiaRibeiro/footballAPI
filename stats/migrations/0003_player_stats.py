# Generated by Django 5.1.1 on 2024-09-29 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0002_player_flag_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='stats',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
