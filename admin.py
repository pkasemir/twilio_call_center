from django.contrib import admin

from .models import TwilioEntry


class TwilioEntryAdmin(admin.ModelAdmin):
    ordering = ['menu_digit']
    list_display = ('enabled', 'menu_digit', 'menu_text', 'action_phone')
    list_display_links = list_display


admin.site.register(TwilioEntry, TwilioEntryAdmin)
