from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Menu, MenuItem, Voice
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
                ["phone", "phone"],
                ["text", "text"],
                ["submenu", "submenu"],
                ["url", "url"],
                ]

    def queryset(self, request, queryset):
        return queryset


class MenuItemAdmin(admin.ModelAdmin):
    ordering = ['menu', 'menu_digit']
    list_filter = ['enabled', 'menu', MenuItemInfoFilter]
    search_fields = ['menu__name', 'menu_text', 'action_text', 'action_url']

    def get_list_display(self, request):
        query_dict = get_query_dict(request)
        info = query_dict.get('info', None)
        common_info = ['enabled', link_to_object('menu'), 'menu_digit', 'menu_text']
        if info == 'phone':
            return common_info + ['action_phone']
        if info == 'text':
            return common_info + ['action_text']
        if info == 'submenu':
            return common_info + [link_to_object('action_submenu', 'menu')]
        if info == 'url':
            return common_info + ['action_url']
        return common_info + ['action_phone', 'action_text', 'action_url',
                link_to_object('action_submenu', 'menu')]

    def get_list_display_links(self, request, list_display):
        return list_display


admin.site.register(Voice)
admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
