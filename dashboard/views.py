from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, DecimalField, ExpressionWrapper 
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import Product, Category, Unit
from .forms import ProductForm, CategoryForm, UnitForm
import json
from pos.models import POSSaleItem,POSSale

# Create your views here.
def _topnav_stats():
    total_sales_amount = (
        POSSale.objects.filter(is_cancelled=False)
        .aggregate(total=Sum('total_amount'))
        .get('total') or 0
    )

    total_product_pieces = (
        Product.objects.aggregate(total=Sum('quantity')).get('total') or 0
    )

    total_orders = POSSale.objects.filter(is_cancelled=False).count()

    total_cost_stock = (
    Product.objects.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('cost_price') * F('quantity'),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            )
        )
    ).get('total') or 0
)
    total_expected_profit_stock = (
    Product.objects.aggregate(
        total=Sum(
            ExpressionWrapper(
                (F('selling_price') - F('cost_price')) * F('quantity'),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            )
        )
    ).get('total') or 0
)

    return {
        "nav_total_sales_amount": total_sales_amount,
        "nav_total_product_pieces": total_product_pieces,
        "nav_total_orders": total_orders,
        "nav_total_cost_stock": total_cost_stock,
        "nav_total_expected_profit_stock": total_expected_profit_stock,
    }

def index(request):
    qs = (
        POSSaleItem.objects
        .filter(sale__is_cancelled=False)  # ถ้าไม่มีฟิลด์นี้ ให้ลบบรรทัดนี้
        .values('product__category__name')
        .annotate(total_amount=Sum('total_price'))
        .order_by('-total_amount')
    )

    labels = [row['product__category__name'] or 'ไม่ระบุหมวดหมู่' for row in qs]
    amounts = [float(row['total_amount'] or 0) for row in qs]

    context = {
        'cat_labels': json.dumps(labels, ensure_ascii=False),
        'cat_amounts': json.dumps(amounts),
        **_topnav_stats(),
    }
    return render(request, 'dashboard/index.html', context)

def product(request):
    
    products = Product.objects.all()
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            
            return redirect('dashboard-product')
    else:  
        form = ProductForm()
    
    context = {
    'products': products,
    'form': form,
    **_topnav_stats(),

    }
    return render(request, 'dashboard/product.html', context)

def edit_product(request, pk):
    """Edit product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('dashboard-product')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'is_edit': True,
        **_topnav_stats(),

    }
    return render(request, 'dashboard/product.html', context)

def delete_product(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('dashboard-product')
    return render(request, 'dashboard/product.html', {'product': product})

def add_category(request):
    """Display all categories"""
    categories = Category.objects.all()
    form = CategoryForm()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard-category')
    else:  
        form = CategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
        **_topnav_stats(),

    }
    return render(request, 'dashboard/category.html', context)

def delete_category(request, pk):
    """Delete a category"""
    category = Category.objects.get(pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('dashboard-category') 
    return render(request, 'dashboard/category.html', {'item': category})

def add_unit(request):
    """Display all units with inline add unit form"""
    units = Unit.objects.all()
    
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard-unit')
    else:  
        form = UnitForm()
    
    context = {
        'units': units,
        'form': form,
        **_topnav_stats(),

    }
    return render(request, 'dashboard/unit.html', context)

def delete_unit(request, pk):
    """Delete a unit"""
    unit = Unit.objects.get(pk=pk)
    if request.method == 'POST':
        unit.delete()
        return redirect('dashboard-unit') 
    return render(request, 'dashboard/unit.html', {'item': unit})

from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from pos.models import POSSaleItem

def sales_summary(request):
    profit_expr = ExpressionWrapper(
        (F('product__selling_price') - F('product__cost_price')) * F('quantity'),
        output_field=DecimalField(max_digits=14, decimal_places=2)
    )

    summary = (
        POSSaleItem.objects
        .filter(sale__is_cancelled=False)
        .values('product__id', 'product__name', 'product__category__name')
        .annotate(
            total_qty=Sum('quantity'),
            total_amount=Sum('total_price'),
            total_profit=Sum(profit_expr),
        )
        .order_by('-total_profit')
    )

    total_profit_all = (
        POSSaleItem.objects
        .filter(sale__is_cancelled=False)
        .aggregate(total=Sum(profit_expr))
        .get('total') or 0
    )

    total_sales_all = (
        POSSaleItem.objects
        .filter(sale__is_cancelled=False)
        .aggregate(total=Sum('total_price'))
        .get('total') or 0
    )

    context = {
        'summary': summary,
        'total_profit_all': total_profit_all,
        'total_sales_all': total_sales_all,
        **_topnav_stats(),

    }
    return render(request, 'dashboard/summary.html', context)
