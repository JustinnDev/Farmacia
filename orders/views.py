from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Order, OrderItem, Payment, Delivery, Review
from .forms import OrderForm, PaymentForm, ReviewForm
from .cart import Cart
from products.models import Product
from users.models import ClientProfile


@login_required
def cart_detail(request):
    """Vista del carrito de compras"""
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})


@login_required
def cart_add(request, product_id):
    """Agregar producto al carrito"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.add(product=product, quantity=quantity)
        messages.success(request, f'{product.name} agregado al carrito.')
        return redirect('orders:cart_detail')

    return render(request, 'orders/cart_add.html', {'product': product})


@login_required
def cart_remove(request, product_id):
    """Remover producto del carrito"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f'{product.name} removido del carrito.')
    return redirect('orders:cart_detail')


@login_required
def checkout(request):
    """Vista de checkout"""
    cart = Cart(request)
    if not cart:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('products:product_list')

    client_profile = get_object_or_404(ClientProfile, user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Crear la orden
            order = Order.objects.create(
                client=client_profile,
                pharmacy=cart.get_pharmacy(),  # Método del carrito para obtener farmacia
                subtotal=cart.get_total_price(),
                total=cart.get_total_price(),  # Por ahora sin delivery fee
                delivery_type=form.cleaned_data['delivery_type'],
                delivery_address=form.cleaned_data['delivery_address'],
                delivery_instructions=form.cleaned_data.get('delivery_instructions', ''),
                payment_deadline=timezone.now() + timedelta(hours=24),  # 24 horas para pagar
            )

            # Crear items de la orden
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    total_price=item['total_price'],
                )

            # Limpiar carrito
            cart.clear()

            messages.success(request, f'Orden #{order.order_number} creada exitosamente.')
            return redirect('orders:payment', order_id=order.id)
    else:
        form = OrderForm()

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'form': form,
        'client_profile': client_profile,
    })


@login_required
def payment(request, order_id):
    """Vista de pago de orden"""
    order = get_object_or_404(Order, id=order_id, client__user=request.user)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']

            # Crear pago
            payment = Payment.objects.create(
                order=order,
                payment_method=payment_method,
                amount=order.total,
                c2p_phone=form.cleaned_data.get('c2p_phone'),
                c2p_reference=form.cleaned_data.get('c2p_reference'),
            )

            # Simular procesamiento de pago
            if payment_method == 'c2p':
                # En producción, aquí iría la integración real con C2P
                payment.is_successful = True
                payment.payment_date = timezone.now()
                payment.transaction_id = f"C2P-{order.order_number}"
                payment.save()

                # Actualizar estado de la orden
                order.payment_status = 'completed'
                order.order_status = 'paid'
                order.save()

                messages.success(request, 'Pago procesado exitosamente.')
                return redirect('orders:order_detail', order_id=order.id)
            else:
                messages.info(request, 'Pago pendiente de verificación.')
                return redirect('orders:order_detail', order_id=order.id)
    else:
        form = PaymentForm()

    return render(request, 'orders/payment.html', {
        'order': order,
        'form': form,
    })


@login_required
def order_detail(request, order_id):
    """Vista detallada de una orden"""
    order = get_object_or_404(Order, id=order_id, client__user=request.user)

    # Verificar si se puede dejar reseña
    can_review = order.order_status == 'delivered' and not hasattr(order, 'review')

    context = {
        'order': order,
        'can_review': can_review,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def order_list(request):
    """Lista de órdenes del usuario"""
    if request.user.user_type == 'client':
        client_profile = get_object_or_404(ClientProfile, user=request.user)
        orders = Order.objects.filter(client=client_profile).order_by('-created_at')
    else:
        # Para farmacias, mostrar órdenes de sus productos
        pharmacy_profile = get_object_or_404(PharmacyProfile, user=request.user)
        orders = Order.objects.filter(pharmacy=pharmacy_profile).order_by('-created_at')

    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def delivery_status(request, order_id):
    """Vista del estado de entrega"""
    order = get_object_or_404(Order, id=order_id, client__user=request.user)
    delivery = get_object_or_404(Delivery, order=order)

    return render(request, 'orders/delivery_status.html', {
        'order': order,
        'delivery': delivery,
    })
