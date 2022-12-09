from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, \
    validate_slug
from django.utils import timezone


twilio_default_transfer = 'Transferring, please wait.'
twilio_default_voice = 'woman'


class Voice(models.Model):
    voice = models.CharField(
        help_text='Twilio voice (ex: man, woman).',
        max_length=40)

    def __str__(self):
        return self.voice


class Menu(models.Model):
    enabled = models.BooleanField(default=True)
    name = models.CharField(
        help_text='The name of the menu, used as the url.',
        validators=[validate_slug],
        max_length=40, unique=True)
    greeting_text = models.CharField(
        help_text='The text to say when entering this menu.',
        max_length=400, blank=True, null=True)
    voice = models.ForeignKey(Voice, on_delete=models.SET_NULL,
        help_text='Twilio voice, if unset default to "' +
            twilio_default_voice + '".',
        blank=True, null=True)

    def __str__(self):
        return self.name


class MailboxNumber(models.Model):
    name = models.CharField(max_length=40)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email_list = models.TextField(blank=True, null=True)
    available_start = models.TimeField(blank=True, null=True)
    available_stop = models.TimeField(blank=True, null=True)
    always_send_voicemail = models.BooleanField(default=False)

    def __str__(self):
        return "{}-{}".format(self.name, self.phone)

    def should_send_voicemail(self):
        if self.always_send_voicemail:
            return True
        if self.phone is None:
            return True
        return self.number_currently_unavailable()

    def number_currently_unavailable(self):
        # if no start/stop time, then always available
        if self.available_start is None:
            return False
        now = timezone.localtime().time()
        return now < self.available_start or now > self.available_stop


class MenuItem(models.Model):
    enabled = models.BooleanField(default=True)
    menu = models.ForeignKey(Menu, on_delete=models.SET_NULL,
        help_text='The menu this item is associated with.',
        related_name='menu_item_set',
        blank=True, null=True)
    menu_digit = models.IntegerField(
        help_text='The key press to access during twilio call.',
        validators=[MinValueValidator(0), MaxValueValidator(9)])
    menu_text = models.CharField(
        help_text='The text to say in the twilio menu. ' +
        'Will be prefixed with "Press N ". ' +
        'If left blank, it will be a hidden menu.',
        max_length=200, blank=True, null=True)
    action_text = models.CharField(
        help_text='The text to say when selected by twilio menu. If action ' +
        'mailbox phone is specified and this is blank, will use ' +
        '"' + twilio_default_transfer + '".',
        max_length=400, blank=True, null=True)
    action_phone = models.CharField(
        help_text='If specified, will transfer to this number when selected by twilio menu.',
        max_length=15, blank=True, null=True)
    action_mailbox = models.ForeignKey(
            MailboxNumber, on_delete=models.SET_NULL,
            help_text='If specified, will transfer to this number or mailbox',
            blank=True, null=True)
    action_submenu = models.ForeignKey(Menu, on_delete=models.SET_NULL,
        help_text='If specified, will send twilio to this submenu.',
        related_name='submenu_item_set',
        blank=True, null=True)
    action_url = models.CharField(
        help_text='If specified, will send twilio to this url.',
        max_length=400, blank=True, null=True)

    def __str__(self):
        return "{}-{}".format(self.menu, self.menu_digit)


class Voicemail(models.Model):
    sid = models.CharField(max_length=40, unique=True)
    call_sid = models.CharField(max_length=40, unique=True)
    menu_item = models.ForeignKey(
            MenuItem, on_delete=models.SET_NULL,
            help_text='The specific menu item used to send this message',
            blank=True, null=True)
    mailbox = models.ForeignKey(
            MailboxNumber, on_delete=models.SET_NULL,
            help_text='The specific mailbox the message was sent to',
            blank=True, null=True)
    from_phone = models.CharField(max_length=20, blank=False, null=False)
    to_phone = models.CharField(max_length=20, blank=False, null=False)
    transcription = models.TextField(
            help_text='A transcription of the recorded message',
            blank=True, null=True)
    url = models.CharField(
            help_text='The url to the recording',
            max_length=256)
    status = models.CharField(max_length=32)
    last_activity = models.DateTimeField()

    def __str__(self):
        return self.sid