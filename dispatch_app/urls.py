from django.urls import path
from . import views

urlpatterns = [
    # Home and Dispatch URLs
    path('', views.home, name='home'),
    path('dispatch/<int:dispatch_id>/', views.dispatch_note, name='dispatch_note'),
    path('dispatch/create/', views.DispatchCreateView.as_view(), name='dispatch_create'),
    path('dispatch/<int:pk>/edit/', views.DispatchUpdateView.as_view(), name='dispatch_edit'),
    path('dispatch/<int:pk>/delete/', views.DispatchDeleteView.as_view(), name='dispatch_delete'),
    path('dispatch/<int:dispatch_id>/loading-sheet/', views.loading_sheet, name='loading_sheet'),
    path('dispatch/<int:dispatch_id>/pallet-labels/', views.pallet_labels, name='pallet_labels'),
    path('reports/', views.reports, name='reports'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<str:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<str:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<str:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Customer URLs
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    
    # AJAX URLs
    path('ajax/customer/<int:customer_id>/', views.get_customer_details, name='get_customer_details'),
    path('ajax/product/<str:product_code>/', views.get_product_details, name='get_product_details'),
]