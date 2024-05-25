# Generated by Django 3.2.25 on 2024-05-25 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_models', '0004_speaker_telegram_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='created_at',
            new_name='created_on',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='updated_at',
            new_name='updated_on',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='created_at',
            new_name='created_on',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='updated_at',
            new_name='updated_on',
        ),
        migrations.RenameField(
            model_name='speaker',
            old_name='created_at',
            new_name='created_on',
        ),
        migrations.RenameField(
            model_name='speaker',
            old_name='updated_at',
            new_name='updated_on',
        ),
    ]