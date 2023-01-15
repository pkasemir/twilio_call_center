from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .apps import my_app
from .models import Menu, MenuItem, Voice, Voicemail, MailboxNumber
from .views import call_reverse, get_query_dict


def link_to_object(member, model=None):
    if model is None:
        model = member
    def _link_to_object(obj):
        obj_member = getattr(obj, member)
        if callable(obj_member):
            obj_member = obj_member()
        if obj_member:
            link = reverse("admin:twilio_call_center_{}_change".format(model),
                           args=[obj_member.pk])
            return format_html('<a href="{}">{}</a>', link, obj_member)
        return '-'
    _link_to_object.__name__ = member
    return _link_to_object


def clean_mutually_exclusive(form, cleaned_data, fields, error):
    mutual_errors = []

    for field in fields:
        if cleaned_data[field] is not None:
            mutual_errors.append(field)

    if len(mutual_errors) > 1:
        for field in mutual_errors:
            form.add_error(field, error)


class MailboxNumberAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'available_start', 'available_stop',
                    'always_send_voicemail']
    search_fields = list_display
    list_display_links = list_display

    def clean(self):
        cleaned_data = super().clean()
        clean_mutually_exclusive(
                self, cleaned_data,
                ['available_start', 'available_stop'],
                'Must specify either both or neither available times')


class VoicemailAdmin(admin.ModelAdmin):
    list_display = [link_to_object('menu_item', 'menuitem'),
                    link_to_object('mailbox', 'mailboxnumber'),
                    'from_phone', 'transcription', 'play_voicemail']
    search_fields = ['from_phone', 'transcription']
    list_display_links = search_fields
    list_filter = ['mailbox']

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in Voicemail._meta.fields]
        return ['_url' if f == 'url' else f
                for f in fields
                if f not in ['id', 'transcription']]

    def get_fields(self, request, obj):
        fields = super().get_fields(request, obj)
        return [f for f in fields if f != 'url']

    def _url(self, obj):
        return format_html(
'''
<a href="{0}.mp3">MP3 Link</a> ---
<a href="{0}">WAV Link</a><br>
{1}
'''.format(obj.url, self.play_voicemail(obj)))

    def play_voicemail(self, obj):
        return format_html(
'''
<audio controls>
  <source src="{0}.mp3" type="audio/mpeg" />
  <source src="{0}" type="audio/wav" />
</audio>
'''.format(obj.url))


class MenuAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'name', 'webhook', link_to_object('voice'), 'menu_items')
    list_display_links = list_display

    def webhook(self, obj):
        link = call_reverse(obj.name, "call-menu")
        return format_html('<a href="{}">{}</a>', link, "link")

    def menu_items(self, obj):
        items = obj.menu_item_set.all()
        link = reverse("admin:twilio_call_center_menuitem_changelist") + \
            "?menu__id__exact={}".format(obj.pk)
        return format_html('<a href="{}">{}</a>', link, "{} items".format(len(items)))


class MenuItemInfoFilter(admin.SimpleListFilter):
    title = 'information'
    parameter_name = 'info'

    def lookups(self, request, model_admin):
        return [
                ["mailbox", "mailbox"],
                ["text", "text"],
                ["submenu", "submenu"],
                ["url", "url"],
                ]

    def queryset(self, request, queryset):
        return queryset


def get_action_function_choices():
    return [('', '---------')] + \
            [(k, k) for k in sorted(my_app().action_functions.keys())]


class MenuItemAdminForm(forms.ModelForm):
    action_function = forms.ChoiceField(
            choices=get_action_function_choices,
            required=False,
            help_text=MenuItem._meta.get_field('action_function').help_text)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['action_function'] == '':
            cleaned_data['action_function'] = None
        clean_mutually_exclusive(
                self, cleaned_data,
                ['action_mailbox', 'action_submenu', 'action_url',
                 'action_function'],
                'Must specify only one action (mailbox, submenu, url, function)')


class MenuItemAdmin(admin.ModelAdmin):
    form = MenuItemAdminForm
    ordering = ['menu', 'menu_digit']
    list_filter = ['enabled', 'menu', MenuItemInfoFilter]
    search_fields = ['menu__name', 'menu_text', 'action_text', 'action_url']

    def get_list_display(self, request):
        query_dict = get_query_dict(request)
        info = query_dict.get('info', None)
        common_info = ['enabled', link_to_object('menu'), 'menu_digit', 'menu_text']
        if info == 'mailbox':
            return common_info + [link_to_object('action_mailbox', 'mailboxnumber')]
        if info == 'text':
            return common_info + ['action_text']
        if info == 'submenu':
            return common_info + [link_to_object('action_submenu', 'menu')]
        if info == 'url':
            return common_info + ['action_url']
        return common_info + [link_to_object('action_mailbox', 'mailboxnumber'),
                'action_text', 'action_url',
                link_to_object('action_submenu', 'menu')]

    def get_list_display_links(self, request, list_display):
        return list_display


class SmsMessageAdmin(admin.ModelAdmin):
    list_display = ['sid', 'from_phone', 'to_phone', 'status', 'last_activity',
                    'message']
    search_fields = list_display
    list_display_links = list_display

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Voice)
admin.site.register(MailboxNumber, MailboxNumberAdmin)
admin.site.register(Voicemail, VoicemailAdmin)
admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(SmsMessage, SmsMessageAdmin)
