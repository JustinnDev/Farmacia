from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('search/', views.product_search, name='product_search'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('create/', views.product_create, name='product_create'),
    path('<int:product_id>/update/', views.product_update, name='product_update'),
    path('<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('pharmacy/products/', views.pharmacy_products, name='pharmacy_products'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('nearby-pharmacies/', views.nearby_pharmacies, name='nearby_pharmacies'),
]