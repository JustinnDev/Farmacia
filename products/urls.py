from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('search/', views.product_search, name='product_search'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
]