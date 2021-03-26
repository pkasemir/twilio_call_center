from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


twilio_default_transfer = 'Transferring, please wait.'


class MenuItem(models.Model):
    enabled = models.BooleanField(default=True)
    menu_digit = models.IntegerField(
        help_text='The key press to access during twilio call.',
        validators=[MinValueValidator(0), MaxValueValidator(9)])
    menu_text = models.CharField(
        help_text='The text to say in the twilio menu. ' +
        'Will be prefixed with "Press N "',
        max_length=200, blank=True, null=True)
    action_text = models.CharField(
        help_text='The text to say when selected by twilio menu. If action ' +
        'phone is specified and this is blank, will use ' +
        '"' + twilio_default_transfer + '"',
        max_length=400, blank=True, null=True)
    action_phone = models.CharField(
        help_text='If specified, will transfer to this number when selected by twilio menu.',
        max_length=15, blank=True, null=True)
