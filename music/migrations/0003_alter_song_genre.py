# Generated by Django 5.1.6 on 2025-03-05 10:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0002_alter_song_album_alter_song_audio_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='genre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='songs', to='music.genre'),
        ),
    ]
