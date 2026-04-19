from django.urls import path
from . import views


urlpatterns = [
    path('', views.index,name='dashboard-index'),
    #path('staff/',views.staff,name='dashboard-staff'),
    path('product/', views.product, name='dashboard-product'),
    #path('product/add/', views.add_product, name='dashboard-add_product'),
    path('product/<int:pk>/edit/', views.edit_product, name='dashboard-edit-product'),  
    path('product/<int:pk>/delete/', views.delete_product, name='dashboard-delete-product'),  
    path('product/category/', views.add_category, name='dashboard-category'),
    path('category/<int:pk>/delete/', views.delete_category, name='delete-category'),
    path('product/unit/', views.add_unit, name='dashboard-unit'),
    path('unit/<int:pk>/delete/', views.delete_unit, name='delete-unit'),
    #path('order/',views.order,name='dashboard-order'),
    path('sales-summary/', views.sales_summary, name='dashboard-sales-summary'),

    
]
