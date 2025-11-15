from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Customer(models.Model):
    CustomerID = models.AutoField(primary_key=True)
    Customer = models.CharField(max_length=255)
    DispatchTo = models.CharField(max_length=255, blank=True, null=True)
    Address = models.TextField(blank=True, null=True)
    Country = models.CharField(max_length=100, blank=True, null=True)
    ContactNo = models.CharField(max_length=50, blank=True, null=True)
    ContactPerson = models.CharField(max_length=255, blank=True, null=True)
    Status = models.BooleanField(default=True)
    
    def __str__(self):
        return self.Customer
    
    class Meta:
        db_table = 'Customer'

class Products(models.Model):
    Code = models.CharField(primary_key=True, max_length=100)
    LocalCode = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    ParPallet = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    UOM = models.CharField(max_length=50, blank=True, null=True)
    PacInCtn = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    def __str__(self):
        return f"{self.Code} - {self.Description}"
    
    class Meta:
        db_table = 'Products'

class Dispatch(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    DispatchID = models.AutoField(primary_key=True)
    OrderNo = models.CharField(max_length=100, unique=True)
    InvoiceNo = models.CharField(max_length=100, blank=True, null=True)
    Customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    Address = models.TextField(blank=True, null=True)
    Country = models.CharField(max_length=100, blank=True, null=True)
    ContactNo = models.CharField(max_length=50, blank=True, null=True)
    ContactPerson = models.CharField(max_length=255, blank=True, null=True)
    OrderDate = models.DateField()
    LoadingDate = models.DateField(blank=True, null=True)
    DeliveryDate = models.DateField(blank=True, null=True)
    TransportNo = models.CharField(max_length=100, blank=True, null=True)
    DriverName = models.CharField(max_length=255, blank=True, null=True)
    DriverMobile = models.CharField(max_length=50, blank=True, null=True)
    Seal = models.CharField(max_length=100, blank=True, null=True)
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatches_created'  # ✅ Unique reverse name
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatches_updated'  # ✅ Unique reverse name
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispatch {self.DispatchID} - {self.OrderNo}"
    
    class Meta:
        db_table = 'Dispatch'

class DispatchDetails(models.Model):
    ID = models.AutoField(primary_key=True)
    DispatchID = models.ForeignKey(Dispatch, on_delete=models.CASCADE, related_name='details')
    Code = models.ForeignKey(Products, on_delete=models.PROTECT)
    LocalCode = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    UOM = models.CharField(max_length=50, blank=True, null=True)
    PackInCarton = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    Qty = models.DecimalField(max_digits=15, decimal_places=4)
    ParPallet = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ProductionDate = models.DateField(blank=True, null=True)
    ExpairyDate = models.DateField(blank=True, null=True)

    
    def __str__(self):
        return f"Detail {self.ID} for Dispatch {self.DispatchID.DispatchID}"
    
    def calculate_pallets(self):
        """Calculate number of pallets: Qty / ParPallet"""
        if self.ParPallet and self.ParPallet > 0:
            return self.Qty / self.ParPallet
        return None
    
    @property
    def pallets(self):
        """Property to access calculated pallets"""
        return self.calculate_pallets()
    
    def get_par_pallet_value(self):
        """Get ParPallet value from item or product"""
        return self.ParPallet or (self.Code.ParPallet if self.Code else None)
    
    def get_pallet_count(self):
        """Get calculated pallet count"""
        par_pallet = self.get_par_pallet_value()
        if par_pallet and par_pallet > 0:
            return self.Qty / par_pallet
        return None
    
    class Meta:
        db_table = 'DispatchDetails'


