from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, \
    validate_slug


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
        'phone is specified and this is blank, will use ' +
        '"' + twilio_default_transfer + '".',
        max_length=400, blank=True, null=True)
    action_phone = models.CharField(
        help_text='If specified, will transfer to this number when selected by twilio menu.',
        max_length=15, blank=True, null=True)
    action_submenu = models.ForeignKey(Menu, on_delete=models.SET_NULL,
        help_text='If specified, will send twilio to this submenu.',
        related_name='submenu_item_set',
        blank=True, null=True)
    action_url = models.CharField(
        help_text='If specified, will send twilio to this url.',
        max_length=400, blank=True, null=True)
