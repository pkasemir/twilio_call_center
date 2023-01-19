from django.urls import path

from . import views
from .schedule import one_time_startup

app_name = 'twilio_call_center'
urlpatterns = [
    path('send-sms', views.SendSmsView.as_view(), name='send-sms'),
    path('send-sms-cb', views.send_sms_cb, name='send-sms-cb'),
    path('sms-forward-cb', views.sms_forward_cb, name='sms-forward-cb'),
    path('sms-incoming', views.sms_incoming, name='sms-incoming'),
    path('sms-status', views.sms_status, name='sms-status'),
    path('<slug:name>/call-menu', views.call_menu, name='call-menu'),
    path('<slug:name>/call-action', views.call_action, name='call-action'),
    path('<slug:name>/call-pin/<slug:digit>', views.call_action, name='call-pin'),
    path('<slug:name>/call-end', views.call_end, name='call-end'),
    path('<slug:name>/voicemail/<slug:digit>', views.voicemail, name='voicemail'),
    path('<slug:name>/voicemail-sms-cb/<slug:digit>', views.voicemail_sms_cb,
         name='voicemail-sms-cb'),
]

one_time_startup()
