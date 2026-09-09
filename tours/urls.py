from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('super-admin/upload/', views.admin_upload_image, name='admin_upload'),
    path('meet-the-tribe/', views.meet_the_tribe, name='meet_the_tribe'),
    path('expedition-gallery/', views.gallery, name='expedition_gallery'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('shop/', views.shop_list, name='shop_list'),
    path('shop/cart/', views.cart_detail, name='cart_detail'),
    path('shop/cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('shop/checkout/', views.guest_checkout, name='guest_checkout'),
    path('shop/track/<uuid:token>/', views.guest_order_tracking, name='guest_order_tracking'),
    path('shop/cart/remove-single/<int:product_id>/', views.cart_remove_single, name='cart_remove_single'),
    path('shop/cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('order/status/<uuid:token>/', views.check_payment_status, name='check_payment_status'),
    path('shop/retry-payment/<uuid:token>/', views.retry_mpesa_payment, name='retry_mpesa_payment'),
]
