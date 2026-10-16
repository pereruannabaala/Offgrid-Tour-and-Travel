from django.urls import path
from . import views
from .views import safari_inquiry_view

urlpatterns = [
    path('', views.index, name='index'),
    path('super-admin/upload/', views.admin_upload_image, name='admin_upload'),
    path('meet-the-tribe/', views.meet_the_tribe, name='meet_the_tribe'),
    path('expedition-gallery/', views.gallery, name='expedition_gallery'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('shop/', views.shop_list, name='shop_list'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('shop/<int:product_id>/', views.product_detail, name='product_detail'),
    path('order/status/<uuid:token>/', views.check_payment_status, name='check_payment_status'),
    path('shop/retry-payment/<uuid:token>/', views.retry_mpesa_payment, name='retry_mpesa_payment'),
    path('shop/cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('safari-inquiry/', safari_inquiry_view, name='safari_inquiry'),
    path('checkout/', views.guest_checkout, name='guest_checkout'),
]



