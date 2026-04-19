from django.db import models

#ถึงตัวฉันในวันข้างหน้า
#หน้านี้สำหรับจัดการ model หลังบ้าน category
# Create your models here.
class Category(models.Model):
    #ชื่อประเภทสินค้า
    name = models.CharField(max_length=200)
    #เพิ่มเข้าตอนไหน ห้ามลืม =w=)b
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
class Unit(models.Model):
    
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"
    
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name   
     
    def is_in_stock(self):
        return self.quantity > 0
    
    def is_low_stock(self):
        return 0 < self.quantity < 10
    @property
    def profit_per_unit(self):
        return self.selling_price - self.cost_price
    
    @property
    def profit_margin(self):
        if self.cost_price == 0:
            return 0
        return (self.profit_per_unit / self.cost_price) * 100