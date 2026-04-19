from django.urls import path
from . import views


urlpatterns = [
    path('cashier/', views.cashier, name='cashier'),
     path('search/', views.search_product_api, name='pos-search'),
    path('add-to-cart/', views.add_to_cart_api, name='pos-add'),
    path('update-cart/', views.update_cart_api, name='pos-update'),
    path('remove-from-cart/', views.remove_from_cart_api, name='pos-remove'),
    path('clear-cart/', views.clear_cart_api, name='pos-clear'),
    path('checkout/', views.checkout, name='pos-checkout'),
    path('history/', views.sales_history, name='sales-history'),
    path('receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('receipt/<int:sale_id>/cancel/', views.cancel_receipt, name='cancel-receipt'),
    
]