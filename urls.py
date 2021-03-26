from django.urls import path

from . import views

urlpatterns = [
    path('call-menu', views.call_menu, name='call-menu'),
    path('call-action', views.call_action, name='call-action'),
    path('call-end', views.call_end, name='call-end'),
]
