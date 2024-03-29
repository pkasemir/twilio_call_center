# Generated by Django 4.0.7 on 2022-12-09 18:19

from django.db import migrations, models
import django.db.models.deletion
import twilio_call_center.models


def phone_to_mailbox(apps, schema_editor):
    MailboxNumber = apps.get_model("twilio_call_center", "MailboxNumber")
    MenuItem = apps.get_model("twilio_call_center", "MenuItem")
    db_alias = schema_editor.connection.alias
    for item in MenuItem.objects.using(db_alias).all():
        if item.action_phone is not None:
            mailbox, _ = MailboxNumber.objects.using(db_alias).get_or_create(
                    phone=item.action_phone,
                    defaults={'name': 'NA'})
            item.action_mailbox = mailbox
            item.save()


def mailbox_to_phone(apps, schema_editor):
    MailboxNumber = apps.get_model("twilio_call_center", "MailboxNumber")
    MenuItem = apps.get_model("twilio_call_center", "MenuItem")
    db_alias = schema_editor.connection.alias
    for item in MenuItem.objects.using(db_alias).all():
        if item.action_mailbox is not None:
            phone = item.action_mailbox.phone
            if phone is not None:
                item.action_phone = phone
                item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('twilio_call_center', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailboxNumber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('email_list', models.TextField(blank=True, null=True, validators=[twilio_call_center.models.validate_email_list])),
                ('available_start', models.TimeField(blank=True, null=True)),
                ('available_stop', models.TimeField(blank=True, null=True)),
                ('always_send_voicemail', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='action_text',
            field=models.CharField(blank=True, help_text='The text to say when selected by twilio menu. If action mailbox phone is specified and this is blank, will use "Transferring, please wait.".', max_length=400, null=True),
        ),
        migrations.CreateModel(
            name='Voicemail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sid', models.CharField(max_length=40, unique=True)),
                ('call_sid', models.CharField(max_length=40, unique=True)),
                ('from_phone', models.CharField(max_length=20)),
                ('to_phone', models.CharField(max_length=20)),
                ('transcription', models.TextField(blank=True, help_text='A transcription of the recorded message', null=True)),
                ('url', models.CharField(help_text='The url to the recording', max_length=256)),
                ('status', models.CharField(max_length=32)),
                ('transcription_status', models.CharField(blank=True, max_length=32, null=True)),
                ('last_activity', models.DateTimeField()),
                ('mailbox', models.ForeignKey(blank=True, help_text='The specific mailbox the message was sent to', null=True, on_delete=django.db.models.deletion.SET_NULL, to='twilio_call_center.mailboxnumber')),
                ('menu_item', models.ForeignKey(blank=True, help_text='The specific menu item used to send this message', null=True, on_delete=django.db.models.deletion.SET_NULL, to='twilio_call_center.menuitem')),
            ],
        ),
        migrations.AddField(
            model_name='menuitem',
            name='action_mailbox',
            field=models.ForeignKey(blank=True, help_text='If specified, will transfer to this number or mailbox', null=True, on_delete=django.db.models.deletion.SET_NULL, to='twilio_call_center.mailboxnumber'),
        ),
        migrations.RunPython(phone_to_mailbox, mailbox_to_phone),
        migrations.RemoveField(
            model_name='menuitem',
            name='action_phone',
        ),
    ]
