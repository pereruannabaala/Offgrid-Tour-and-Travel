from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('super-admin/upload/', views.admin_upload_image, name='admin_upload'),
    path('meet-the-tribe/', views.meet_the_tribe, name='meet_the_tribe'),
]