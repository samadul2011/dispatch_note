from multiprocessing import context
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.http import JsonResponse
from .models import Dispatch, DispatchDetails, Customer, Products
from .forms import DispatchForm, DispatchDetailsFormSet, ProductForm, CustomerForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from datetime import date, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal, InvalidOperation
from .forms import DispatchDetailsFormSet, DispatchDetailsEditFormSet
from datetime import datetime
import calendar
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponse


@login_required
def home(request):
    """Home page that lists all dispatches with smart sorting"""
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort_by', '')
    
    # Base queryset
    dispatches = Dispatch.objects.all()
    
    # Apply status filter if provided
    if status and status != 'all':
        dispatches = dispatches.filter(Status=status)
    
    # Apply sorting based on status or explicit sort parameter
    if status == 'draft' or sort_by == 'loading':
        # For drafts, sort by Loading Date (oldest first) to see pending loads
        dispatches = dispatches.order_by('LoadingDate')
    elif sort_by == 'delivery':
        # For delivery view, sort by Delivery Date (newest first)
        dispatches = dispatches.order_by('-DeliveryDate')
    else:
        # Default: sort by Order Date (newest first)
        dispatches = dispatches.order_by('-OrderDate')
    
    # Calculate status counts for the summary
    all_dispatches = Dispatch.objects.all()
    status_counts = {
        'draft': all_dispatches.filter(Status='draft').count(),
        'confirmed': all_dispatches.filter(Status='confirmed').count(),
        'shipped': all_dispatches.filter(Status='shipped').count(),
        'delivered': all_dispatches.filter(Status='delivered').count(),
        'cancelled': all_dispatches.filter(Status='cancelled').count(),
    }
    
    # Dates for highlighting
    today = date.today()
    soon_date = today + timedelta(days=3)
    
    context = {
        'dispatches': dispatches,
        'status_counts': status_counts,
        'total_export': all_dispatches.count(),
        'current_status': status,
        'current_sort': sort_by,
        'today': today,
        'soon_date': soon_date,
    }
    return render(request, 'home.html', context)

def debug_messages(request):
    """Debug view to test messages"""
    messages.success(request, 'This is a success message!')
    messages.error(request, 'This is an error message!')
    messages.warning(request, 'This is a warning message!')
    messages.info(request, 'This is an info message!')
    return redirect('home')

@login_required
def dispatch_note(request, dispatch_id):
    """Individual dispatch note view"""
    dispatch = get_object_or_404(Dispatch, pk=dispatch_id)
    return render(request, 'dispatch_note.html', {'dispatch': dispatch})

def get_customer_details(request, customer_id):
    """Get customer details for auto-fill"""
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        data = {
            'Address': customer.Address or '',
            'Country': customer.Country or '',
            'ContactNo': customer.ContactNo or '',
            'ContactPerson': customer.ContactPerson or '',
            'DispatchTo': customer.DispatchTo or '',
        }
        return JsonResponse(data)
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)

def get_product_details(request, product_code):
    """Get product details for auto-fill"""
    try:
        product = get_object_or_404(Products, Code=product_code)
        data = {
            'LocalCode': product.LocalCode or '',
            'Description': product.Description or '',
            'UOM': product.UOM or '',
            'PackInCarton': str(product.PacInCtn) if product.PacInCtn else '',
            'ParPallet': str(product.ParPallet) if product.ParPallet else '',
        }
        return JsonResponse(data)
    except Products.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@method_decorator(login_required, name='dispatch')
class DispatchCreateView(CreateView):
    model = Dispatch
    form_class = DispatchForm
    template_name = 'dispatch_form.html'
    success_url = reverse_lazy('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DispatchDetailsFormSet(self.request.POST)
        else:
            context['formset'] = DispatchDetailsFormSet()  # extra=1
        return context
    
    def form_valid(self, form):
        formset = DispatchDetailsFormSet(self.request.POST)
        
        with transaction.atomic():
            self.object = form.save()
            
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
                messages.success(self.request, 'Dispatch created successfully!')
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, 'Please correct the errors below.')
                return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user  # ✅ Set creator
        context = self.get_context_data()
        formset = context['formset']
        with transaction.atomic():
            self.object = form.save()
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
                messages.success(self.request, 'Dispatch created successfully!')
                return redirect('home')
            else:
                return self.form_invalid(form)




@method_decorator(login_required, name='dispatch')
class DispatchUpdateView(UpdateView):
    model = Dispatch
    form_class = DispatchForm
    template_name = 'dispatch_form.html'
    success_url = reverse_lazy('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DispatchDetailsEditFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = DispatchDetailsEditFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user  # ✅ Set updater
        formset = DispatchDetailsEditFormSet(self.request.POST, instance=self.object)
        
        with transaction.atomic():
            self.object = form.save()
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
                messages.success(self.request, 'Dispatch updated successfully!')
                return redirect(self.get_success_url())
            else:
                # Debug info (keep during dev)
                print("Formset errors:", formset.errors)
                messages.error(self.request, 'Please correct the errors in product details.')
                return self.form_invalid(form)

@method_decorator(login_required, name='dispatch')    
class DispatchDeleteView(LoginRequiredMixin, DeleteView):
    model = Dispatch
    template_name = 'dispatch_confirm_delete.html'
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        # Only superusers can delete
        if not request.user.is_superuser:
            messages.error(
                request, 
                "You don't have permission for deleting. Only Admin can delete."
            )
            # Redirect back to home or dispatch detail
            return redirect('home')  # or redirect('dispatch_note', pk=self.get_object().DispatchID)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Dispatch deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
# Product Views
@method_decorator(login_required, name='dispatch')
class ProductListView(ListView):
    model = Products
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Products.objects.all().order_by('Code')

@method_decorator(login_required, name='dispatch')
class ProductCreateView(CreateView):
    model = Products
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('product_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Product created successfully!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ProductUpdateView(UpdateView):
    model = Products
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('product_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ProductDetailView(DetailView):
    model = Products
    template_name = 'product_detail.html'

@method_decorator(login_required, name='dispatch')
class ProductDeleteView(DeleteView):
    model = Products
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('product_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Customer Views
@method_decorator(login_required, name='dispatch')
class CustomerListView(ListView):
    model = Customer
    template_name = 'customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        return Customer.objects.all().order_by('Customer')

@method_decorator(login_required, name='dispatch')
class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer_form.html'
    success_url = reverse_lazy('customer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Customer created successfully!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer_form.html'
    success_url = reverse_lazy('customer_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'customer_detail.html'

@method_decorator(login_required, name='dispatch')
class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Customer deleted successfully!')
        return super().delete(request, *args, **kwargs)
# views.py


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

# views.py
#from django.shortcuts import render, get_object_or_404

@login_required
# views.py




def loading_sheet(request, dispatch_id):
    dispatch = get_object_or_404(Dispatch, pk=dispatch_id)
    
    pallet_rows = []
    for item in dispatch.details.all():
        # Skip if Qty is zero, None, or invalid
        if not item.Qty:
            continue
        try:
            total_qty = Decimal(str(item.Qty))
            if total_qty <= 0:
                continue
        except (InvalidOperation, ValueError):
            continue

        # Get ParPallet (from item or product)
        par_pallet = None
        if item.ParPallet:
            par_pallet = item.ParPallet
        elif item.Code and item.Code.ParPallet:
            par_pallet = item.Code.ParPallet

        if not par_pallet:
            # No pallet info → treat as 1 pallet with full qty
            pallet_rows.append({
                'Code': item.Code.Code if item.Code else 'N/A',
                'Description': item.Description or (item.Code.Description if item.Code else ''),
                'ParPallet': None,
                'QtyOnPallet': float(total_qty),
                'ProductionDate': item.ProductionDate,
                'ExpiryDate': item.ExpairyDate,
                'is_partial': False,
            })
            continue

        try:
            par_pallet_dec = Decimal(str(par_pallet))
            if par_pallet_dec <= 0:
                # Invalid pallet size → treat as single pallet
                pallet_rows.append({
                    'Code': item.Code.Code if item.Code else 'N/A',
                    'Description': item.Description or (item.Code.Description if item.Code else ''),
                    'ParPallet': float(par_pallet_dec),
                    'QtyOnPallet': float(total_qty),
                    'ProductionDate': item.ProductionDate,
                    'ExpiryDate': item.ExpairyDate,
                    'is_partial': False,
                })
                continue
        except (InvalidOperation, ValueError):
            continue

        # ✅ Now both are Decimal → safe math
        full_pallets = int(total_qty // par_pallet_dec)
        remainder = total_qty % par_pallet_dec

        # Add full pallets
        for _ in range(full_pallets):
            pallet_rows.append({
                'Code': item.Code.Code,
                'Description': item.Description or item.Code.Description,
                'ParPallet': float(par_pallet_dec),
                'QtyOnPallet': float(par_pallet_dec),
                'ProductionDate': item.ProductionDate,
                'ExpiryDate': item.ExpairyDate,
                'is_partial': False,
            })
        
        # Add partial pallet
        if remainder > 0:
            pallet_rows.append({
                'Code': item.Code.Code,
                'Description': item.Description or item.Code.Description,
                'ParPallet': float(par_pallet_dec),
                'QtyOnPallet': float(remainder),
                'ProductionDate': item.ProductionDate,
                'ExpiryDate': item.ExpairyDate,
                'is_partial': True,
            })
    
    total_pallets = len(pallet_rows)
    trucks_needed = (total_pallets + 21) // 22 if total_pallets > 0 else 0

    context = {
        'dispatch': dispatch,
        'pallet_rows': pallet_rows,
        'total_pallets': total_pallets,
        'trucks_needed': trucks_needed,
    }
    return render(request, 'loading_sheet.html', context)

# views.py
def pallet_labels(request, dispatch_id):
    dispatch = get_object_or_404(Dispatch, pk=dispatch_id)
    
    pallet_rows = []
    for item in dispatch.details.all():
        if not item.Qty:
            continue
        total_qty = Decimal(str(item.Qty))
        par_pallet = item.ParPallet or (item.Code.ParPallet if item.Code else None)

        if not par_pallet or par_pallet <= 0:
            pallet_rows.append({
                'customer': dispatch.Customer.Customer,
                'order_no': dispatch.OrderNo,
                'code': item.Code.Code if item.Code else 'N/A',
                'description': item.Description or (item.Code.Description if item.Code else ''),
                'qty_on_pallet': float(total_qty),
                'production_date': item.ProductionDate,
                'expiry_date': item.ExpairyDate,
            })
            continue

        par_pallet_dec = Decimal(str(par_pallet))
        full_pallets = int(total_qty // par_pallet_dec)
        remainder = total_qty % par_pallet_dec

        for _ in range(full_pallets):
            pallet_rows.append({
                'customer': dispatch.Customer.Customer,
                'order_no': dispatch.OrderNo,
                'code': item.Code.Code,
                'description': item.Description or item.Code.Description,
                'qty_on_pallet': float(par_pallet_dec),
                'production_date': item.ProductionDate,
                'expiry_date': item.ExpairyDate,
            })
        
        if remainder > 0:
            pallet_rows.append({
                'customer': dispatch.Customer.Customer,
                'order_no': dispatch.OrderNo,
                'code': item.Code.Code,
                'description': item.Description or item.Code.Description,
                'qty_on_pallet': float(remainder),
                'production_date': item.ProductionDate,
                'expiry_date': (getattr(item, 'ExpiryDate', None) or getattr(item, 'ExpairyDate', None)),
            })
    
    context = {
        'dispatch': dispatch,
        'pallet_labels': pallet_rows,
    }
    return render(request, 'pallet_labels.html', context)



def reports(request):
    # Get filter parameters
    report_type = request.GET.get('report_type', 'customer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status', '')  # <-- New: status filter
    
    # Default to current month
    if not start_date and not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    else:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Build base queryset with date range
    base_dispatches = Dispatch.objects.filter(OrderDate__range=[start_date, end_date])
    
    # Apply status filter if selected
    if status:
        base_dispatches = base_dispatches.filter(Status=status)

    # Check if we're looking at a specific customer's details
    customer_name = request.GET.get('customer')
    
    if customer_name:
        # Show detailed orders for this customer
        dispatches = Dispatch.objects.filter(
            OrderDate__range=[start_date, end_date],
            Customer__Customer=customer_name
        )
        if status:
            dispatches = dispatches.filter(Status=status)
        
        # Annotate with total quantity for each dispatch
        dispatches = dispatches.annotate(
            total_qty=Sum('details__Qty')
        ).order_by('-OrderDate')
        
        # Excel export for customer details
        if request.GET.get('format') == 'excel':
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws.title = f"{customer_name} Orders"
            
            # Add headers
            ws.append(['Order No', 'Dispatch ID', 'Status', 'Order Date', 'Total Qty'])
            
            # Add data rows
            for d in dispatches:
                total_qty = d.details.aggregate(total=Sum('Qty'))['total'] or 0
                ws.append([d.OrderNo, d.DispatchID, d.Status, d.OrderDate, float(total_qty)])
            
            # Prepare response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename={customer_name}_orders_{timezone.now().strftime("%Y%m%d")}.xlsx'
            wb.save(response)
            return response
        
        context = {
            'is_customer_detail': True,
            'customer_name': customer_name,
            'start_date': start_date,
            'end_date': end_date,
            'status': status,
            'dispatches': dispatches.order_by('-OrderDate'),
            'status_choices': [  # Add status choices for dropdown
                ('', 'All Statuses'),
                ('draft', 'Draft'),
                ('confirmed', 'Confirmed'),
                ('shipped', 'Shipped'),
                ('delivered', 'Delivered'),
                ('cancelled', 'Cancelled'),
            ]
        }
        return render(request, 'reports.html', context)

    # Rest of your report logic using base_dispatches
    if report_type == 'customer':
        data = base_dispatches.values('Customer__Customer').annotate(
            total_dispatches=Count('pk', distinct=True),  # ✅ FIXED
            total_items=Count('details'),
            total_qty=Sum('details__Qty')
        ).order_by('-total_qty')
        columns = ['Customer', 'Total Dispatches', 'Total Items', 'Total Qty']

    elif report_type == 'product':
        # For product report, filter DispatchDetails by status via DispatchID
        data = DispatchDetails.objects.filter(
            DispatchID__in=base_dispatches.values('DispatchID')
        ).values(
            'Code__Code',
            'Code__Description'
        ).annotate(
            total_qty=Sum('Qty')
        ).order_by('-total_qty')
        columns = ['Code', 'Description', 'Total Qty']

    elif report_type == 'monthly':
        data = base_dispatches.extra(
            select={'month': "strftime('%%Y-%%m', OrderDate)"}
        ).values('month').annotate(
            total_dispatches=Count('pk', distinct=True),  # ✅ FIXED
            total_qty=Sum('details__Qty')
        ).order_by('-month')
        columns = ['Month', 'Total Dispatches', 'Total Qty']

    # Excel export logic
    if request.GET.get('format') == 'excel':
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Dispatch Report"
        
        # Add headers
        ws.append(columns)
        
        # Add data rows
        for row in data:
            if report_type == 'customer':
                ws.append([
                    row['Customer__Customer'],
                    row['total_dispatches'] or 0,
                    float(row['total_items'] or 0),
                    float(row['total_qty'] or 0)
                ])
            elif report_type == 'product':
                ws.append([
                    row['Code__Code'],
                    row['Code__Description'],
                    float(row['total_qty'] or 0)
                ])
            elif report_type == 'monthly':
                ws.append([
                    row['month'],
                    row['total_dispatches'] or 0,
                    float(row['total_qty'] or 0)
                ])
        
        # Prepare response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=dispatch_report_{timezone.now().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        return response
    
    # Add status to context
    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,  # <-- Pass to template
        'data': data,
        'columns': columns,
        # Add status choices for dropdown
        'status_choices': [
            ('', 'All Statuses'),
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ]
    }
    
    return render(request, 'reports.html', context)
