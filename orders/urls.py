from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('master-order/<int:master_order_id>/', views.master_order_detail, name='master_order_detail'),
    path('master-orders/', views.master_order_list, name='master_order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_list, name='order_list'),
    path('delivery/<int:order_id>/', views.delivery_status, name='delivery_status'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_status'),
    path('order/<int:order_id>/start-delivery/', views.start_delivery, name='start_delivery'),
]