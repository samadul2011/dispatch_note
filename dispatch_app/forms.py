from django import forms
from .models import Dispatch, DispatchDetails, Customer, Products
from django.forms import inlineformset_factory, BaseInlineFormSet


class CustomDispatchDetailsFormSet(BaseInlineFormSet):
    """Custom formset to skip validation for completely empty rows."""
    def clean(self):
        # Call parent clean but catch any errors we'll fix
        try:
            super().clean()
        except forms.ValidationError:
            pass
        
        # Post-process: remove validation errors from completely empty forms
        for form in self.forms:
            # Skip if marked for deletion
            if form.cleaned_data.get('DELETE'):
                continue
            
            # Check if form is completely empty
            code = form.cleaned_data.get('Code')
            qty = form.cleaned_data.get('Qty')
            
            # If BOTH Code and Qty are empty, this is a blank row - clear errors
            if not code and not qty:
                form.errors.clear()
                # Also clear any non-field errors specific to this form
                if hasattr(form, 'non_field_errors'):
                    pass  # Can't clear these easily, but empty rows won't have them

class DispatchForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = [
            'OrderNo', 'InvoiceNo', 'Customer', 'Address', 'Country',
            'ContactNo', 'ContactPerson', 'OrderDate', 'LoadingDate', 
            'DeliveryDate', 'TransportNo', 'DriverName', 'DriverMobile',
            'Seal', 'Status'
        ]
        widgets = {
            'OrderDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'LoadingDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'DeliveryDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'Address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'Customer': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['Address'] and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

# forms.py
class DispatchDetailsForm(forms.ModelForm):
    class Meta:
        model = DispatchDetails
        fields = [
            'Code', 'LocalCode', 'Description', 'UOM',
            'PackInCarton', 'Qty', 'ParPallet',
            'ProductionDate', 'ExpairyDate'
        ]
        widgets = {
            'Description': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control auto-filled',
                'readonly': 'readonly'
            }),
            'Code': forms.Select(attrs={'class': 'form-control'}),  # editable dropdown
            'LocalCode': forms.TextInput(attrs={
                'class': 'form-control auto-filled',
                'readonly': 'readonly'
            }),
            'UOM': forms.TextInput(attrs={
                'class': 'form-control auto-filled',
                'readonly': 'readonly'
            }),
            'PackInCarton': forms.NumberInput(attrs={
                'class': 'form-control auto-filled',
                'readonly': 'readonly',
                'step': '0.01'
            }),
            'Qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),  # ✅ editable
            'ParPallet': forms.NumberInput(attrs={
                'class': 'form-control auto-filled',
                'readonly': 'readonly',
                'step': '0.01'
            }),
            'ProductionDate': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),  # ✅ editable
            'ExpairyDate': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),  # ✅ editable
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'Code' in self.fields:
            self.fields['Code'].queryset = Products.objects.all()
            self.fields['Code'].empty_label = "Select a product"
        
        # Make non-editable fields not required (since they're auto-filled)
        non_editable_fields = ['LocalCode', 'Description', 'UOM', 'PackInCarton', 'ParPallet']
        for field in non_editable_fields:
            self.fields[field].required = False
            
        self.fields['Code'].required = False
        self.fields['LocalCode'].required = False
        self.fields['Description'].required = False
        self.fields['UOM'].required = False
        self.fields['PackInCarton'].required = False
        self.fields['Qty'].required = False
        self.fields['ParPallet'].required = False
        self.fields['ProductionDate'].required = False
        self.fields['ExpairyDate'].required = False

    def clean(self):
        """Allow completely empty rows (all fields blank) or fully filled rows."""
        cleaned_data = super().clean()
        
        # Check if this form is completely empty
        code = cleaned_data.get('Code')
        qty = cleaned_data.get('Qty')
        local_code = cleaned_data.get('LocalCode')
        description = cleaned_data.get('Description')
        uom = cleaned_data.get('UOM')
        pack_in_carton = cleaned_data.get('PackInCarton')
        par_pallet = cleaned_data.get('ParPallet')
        production_date = cleaned_data.get('ProductionDate')
        expiry_date = cleaned_data.get('ExpairyDate')
        
        # Get all values in a list
        all_values = [code, qty, local_code, description, uom, pack_in_carton, par_pallet, production_date, expiry_date]
        
        # If all fields are empty, allow it (blank row)
        if all(v is None or v == '' for v in all_values):
            return cleaned_data
        
        # If Code or Qty is missing but other fields have values, raise error
        if not code:
            self.add_error('Code', 'Product code is required when adding items.')
        if not qty:
            self.add_error('Qty', 'Quantity is required when adding items.')
        
        return cleaned_data

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['Code', 'LocalCode', 'Description', 'ParPallet', 'UOM', 'PacInCtn']
        widgets = {
            'Description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'Code': forms.TextInput(attrs={'class': 'form-control'}),
            'LocalCode': forms.TextInput(attrs={'class': 'form-control'}),
            'UOM': forms.TextInput(attrs={'class': 'form-control'}),
            'ParPallet': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'PacInCtn': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'Description' and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['Customer', 'DispatchTo', 'Address', 'Country', 'ContactNo', 'ContactPerson', 'Status']
        widgets = {
            'Address': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'Customer': forms.TextInput(attrs={'class': 'form-control'}),
            'DispatchTo': forms.TextInput(attrs={'class': 'form-control'}),
            'Country': forms.TextInput(attrs={'class': 'form-control'}),
            'ContactNo': forms.TextInput(attrs={'class': 'form-control'}),
            'ContactPerson': forms.TextInput(attrs={'class': 'form-control'}),
            'Status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'Address' and field_name != 'Status' and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


# Create inline formset for DispatchDetails
DispatchDetailsFormSet = inlineformset_factory(
    Dispatch,
    DispatchDetails,
    form=DispatchDetailsForm,
    formset=CustomDispatchDetailsFormSet,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=['Code', 'LocalCode', 'Description', 'UOM', 'PackInCarton', 'Qty', 'ParPallet', 'ProductionDate', 'ExpairyDate']
)

# FormSet variant for editing (no extra blank form)
DispatchDetailsEditFormSet = inlineformset_factory(
    Dispatch,
    DispatchDetails,
    form=DispatchDetailsForm,
    formset=CustomDispatchDetailsFormSet,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=['Code', 'LocalCode', 'Description', 'UOM', 'PackInCarton', 'Qty', 'ParPallet', 'ProductionDate', 'ExpairyDate']
)