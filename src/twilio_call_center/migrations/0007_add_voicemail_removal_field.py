# Generated by Django 4.0.7 on 2023-01-19 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twilio_call_center', '0006_add_sms_twilio_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='voicemail',
            name='removed_from_twilio',
            field=models.BooleanField(default=False),
        ),
    ]
