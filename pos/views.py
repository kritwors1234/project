from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q,Sum
from dashboard.models import Product
from .models import POSSale, POSSaleItem

import json
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

    return {
        "nav_total_sales_amount": total_sales_amount,
        "nav_total_product_pieces": total_product_pieces,
        "nav_total_orders": total_orders,
    }

def cashier(request):
    """หน้า POS Cashier"""
    products = Product.objects.filter(quantity__gt=0)
    cart = request.session.get('pos_cart', {})
    total = sum(float(item['total']) for item in cart.values())
    
    context = {
        'products': products,
        'cart': cart,
        'total': total,
        'cart_count': len(cart),
        **_topnav_stats(),
    }
    return render(request, 'pos/cashier.html', context)

def search_product_api(request):
    """ค้นหาสินค้า (AJAX API)"""
    query = request.GET.get('q', '')
    
    if len(query) < 1:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(sku__icontains=query) |
        Q(category__name__icontains=query),
        quantity__gt=0
    )[:15]
    
    data = {
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'price': float(p.selling_price),
                'cost': float(p.cost_price),
                'quantity': p.quantity,
                'category': p.category.name if p.category else 'N/A',
                'unit': p.unit.symbol if p.unit else '',
            }
            for p in products
        ]
    }
    return JsonResponse(data)

def add_to_cart_api(request):
    """เพิ่มสินค้าลงตะกร้า (AJAX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            
            if product.quantity < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Stock ไม่พอ! เหลือ {product.quantity} ชิ้น'
                })
            
            cart = request.session.get('pos_cart', {})
            product_id_str = str(product_id)
            
            if product_id_str in cart:
                new_qty = cart[product_id_str]['quantity'] + quantity
                if product.quantity < new_qty:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Stock ไม่พอ! เหลือ {product.quantity} ชิ้น'
                    })
                cart[product_id_str]['quantity'] = new_qty
                cart[product_id_str]['total'] = float(cart[product_id_str]['price']) * new_qty
            else:
                cart[product_id_str] = {
                    'id': product_id,
                    'name': product.name,
                    'sku': product.sku,
                    'price': float(product.selling_price),
                    'quantity': quantity,
                    'total': float(product.selling_price) * quantity,
                    'unit': product.unit.symbol if product.unit else '',
                }
            
            request.session['pos_cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'message': f'{product.name} เพิ่มลงตะกร้าแล้ว',
                'cart_count': len(cart),
                'total': sum(float(item['total']) for item in cart.values())
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Product not found'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def remove_from_cart_api(request):
    """ลบสินค้าจากตะกร้า (AJAX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        cart = request.session.get('pos_cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            del cart[product_id_str]
            request.session['pos_cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'cart_count': len(cart),
                'total': sum(float(item['total']) for item in cart.values())
            })
        
        return JsonResponse({
            'status': 'error',
            'message': 'Item not found'
        })

def clear_cart_api(request):
    """ลบสินค้าทั้งหมด (AJAX)"""
    request.session['pos_cart'] = {}
    request.session.modified = True
    
    return JsonResponse({
        'status': 'success',
        'cart_count': 0,
        'total': 0
    })

def checkout(request):
    """ชำระเงิน"""
    if request.method == 'POST':
        cart = request.session.get('pos_cart', {})
        
        if not cart:
            messages.error(request, 'ตะกร้าว่าง')
            return redirect('cashier')
        
        #คำนวณเงิน (เพียง total เท่านั้น)
        total_amount = sum(float(item['total']) for item in cart.values())
        
        
        # สร้าง Sale
        sale = POSSale.objects.create(
            #epoch 1970-01-01
            sale_no=f"POS-{int(timezone.now().timestamp())}",
            
            total_amount=total_amount,
        )
        
        # สร้าง SaleItem และลด Stock
        for product_id_str, item in cart.items():
            try:
                product = Product.objects.get(id=product_id_str)
                
                POSSaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    total_price=item['total']
                )
                
                # ลด Stock
                product.quantity -= item['quantity']
                product.save()
                
            except Product.DoesNotExist:
                pass
        
        # ลบ Cart
        request.session['pos_cart'] = {}
        request.session.modified = True
        
        messages.success(request, f'Receipt เลขที่ {sale.sale_no}')
        return redirect('receipt', sale_id=sale.id)
    
    return redirect('cashier')

def receipt(request, sale_id):
    """ใบเสร็จการขาย"""
    sale = get_object_or_404(POSSale, id=sale_id)
    context = {'sale': sale,
               **_topnav_stats(),
               }
    return render(request, 'pos/receipt.html', context)




def update_cart_api(request):
    """อัปเดตจำนวนสินค้า (AJAX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            
            # ตรวจสอบ Stock
            if product.quantity < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Stock ไม่พอ! เหลือ {product.quantity} ชิ้น'
                })
            
            cart = request.session.get('pos_cart', {})
            product_id_str = str(product_id)
            
            if product_id_str in cart:
                cart[product_id_str]['quantity'] = quantity
                cart[product_id_str]['total'] = float(cart[product_id_str]['price']) * quantity
                request.session['pos_cart'] = cart
                request.session.modified = True
                
                return JsonResponse({
                    'status': 'success',
                    'total': sum(float(item['total']) for item in cart.values())
                })
            
            return JsonResponse({
                'status': 'error',
                'message': 'Item not found'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Product not found'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def sales_history(request):
    sales = POSSale.objects.all().order_by('-created_at')
    return render(request, 'dashboard/order.html', {'sales': sales,**_topnav_stats(),})

@require_POST
@transaction.atomic
def cancel_receipt(request, sale_id):
    sale = get_object_or_404(POSSale, id=sale_id)

    # กันยกเลิกซ้ำ
    if sale.is_cancelled:
        messages.warning(request, 'บิลนี้ถูกยกเลิกไปแล้ว')
        return redirect('receipt', sale_id=sale.id)

    # คืนสต็อก
    for item in sale.items.select_related('product').all():
        product = item.product
        product.quantity += item.quantity
        product.save()

    #ตั้งสถานะยกเลิก
    sale.is_cancelled = True
    sale.cancelled_at = timezone.now()
    sale.save()

    messages.success(request, f'ยกเลิกบิล {sale.sale_no} เรียบร้อยแล้ว')
    return redirect('receipt', sale_id=sale.id)