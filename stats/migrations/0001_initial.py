# Generated by Django 5.1.1 on 2024-09-28 22:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('crest', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('player_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('position', models.CharField(max_length=50)),
                ('nationality', models.CharField(max_length=50)),
                ('image', models.URLField(blank=True, null=True)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='stats.team')),
            ],
        ),
    ]
