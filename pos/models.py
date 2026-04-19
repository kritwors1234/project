from django.db import models
from dashboard.models import Product

class POSSale(models.Model):
    """ใบขาย POS"""
    sale_no = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.sale_no
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sale_no} - ฿{self.total_amount}"


class POSSaleItem(models.Model):
    """รายการสินค้าในใบขาย"""
    sale = models.ForeignKey(POSSale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
# Create your models here.
