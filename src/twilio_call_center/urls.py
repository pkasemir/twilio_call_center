from django.urls import path

from . import views

app_name = 'twilio_call_center'
urlpatterns = [
    path('<slug:name>/call-menu', views.call_menu, name='call-menu'),
    path('<slug:name>/call-action', views.call_action, name='call-action'),
    path('<slug:name>/call-pin/<slug:digit>', views.call_action, name='call-pin'),
    path('<slug:name>/call-end', views.call_end, name='call-end'),
    path('<slug:name>/voicemail/<slug:digit>', views.voicemail, name='voicemail'),
]
