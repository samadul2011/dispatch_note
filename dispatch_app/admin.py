# admin.py
from django.contrib import admin
from .models import Customer, Products, Dispatch, DispatchDetails

class DispatchDetailsInline(admin.TabularInline):
    model = DispatchDetails
    extra = 1

    def has_add_permission(self, request, obj=None):
        # Staff and superusers can add items
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        # ❗ Only superusers can delete line items
        return request.user.is_superuser


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['CustomerID', 'Customer', 'ContactPerson', 'Country', 'Status']
    
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['Code', 'LocalCode', 'Description', 'UOM']
    
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = ['DispatchID', 'OrderNo', 'Customer', 'OrderDate', 'Status']
    inlines = [DispatchDetailsInline]

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        # ONLY superusers can delete
        return request.user.is_superuser

    def get_actions(self, request):
        # Remove bulk delete for non-superusers
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop('delete_selected', None)
        return actions
