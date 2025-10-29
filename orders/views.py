from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import MasterOrder, Order, OrderItem, Payment, Delivery, Review
from .forms import OrderForm, PaymentForm, ReviewForm
from .cart import Cart
from products.models import Product
from users.models import ClientProfile
from users.decorators import pharmacy_required


@login_required
def cart_detail(request):
    """Vista del carrito de compras"""
    cart = Cart(request)
    cart_total = cart.get_total_price()
    return render(request, 'orders/cart_detail.html', {
        'cart': cart,
        'cart_total': cart_total,
    })


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
            # Crear orden maestra
            master_order = MasterOrder.objects.create(
                client=client_profile,
                total_amount=cart.get_total_price(),
            )

            # Agrupar productos por farmacia
            pharmacies = cart.get_pharmacies()

            for pharmacy_id, items in pharmacies.items():
                from users.models import PharmacyProfile
                pharmacy = PharmacyProfile.objects.get(id=pharmacy_id)

                # Calcular subtotal para esta farmacia
                subtotal = sum(Decimal(item['price']) * item['quantity'] for item in items)

                # Crear sub-orden
                sub_order = Order.objects.create(
                    master_order=master_order,
                    client=client_profile,
                    pharmacy=pharmacy,
                    subtotal=subtotal,
                    total=subtotal,  # Sin delivery fee por ahora
                    delivery_type=form.cleaned_data['delivery_type'],
                    delivery_address=form.cleaned_data['delivery_address'],
                    delivery_instructions=form.cleaned_data.get('delivery_instructions', ''),
                    payment_deadline=timezone.now() + timedelta(hours=24),
                )

                # Crear items para esta sub-orden
                for item in items:
                    # Obtener el producto desde la base de datos usando el product_id
                    product_id = item['product_id']
                    product = Product.objects.get(id=product_id)

                    # Calcular total_price si no existe
                    unit_price = Decimal(item['price'])
                    quantity = item['quantity']
                    total_price = unit_price * quantity

                    OrderItem.objects.create(
                        order=sub_order,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                    )

            # Limpiar carrito
            cart.clear()

            messages.success(request, f'Orden #{master_order.master_order_number} creada exitosamente.')
            return redirect('orders:master_order_detail', master_order_id=master_order.id)
    else:
        form = OrderForm()

    # Variables calculadas para el template
    cart_total = cart.get_total_price()
    pharmacy_info = cart.get_pharmacies()  # Mostrar todas las farmacias

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'form': form,
        'client_profile': client_profile,
        'cart_total': cart_total,
        'pharmacy_info': pharmacy_info,
    })


@login_required
def payment(request, order_id):
    """Vista de pago de orden"""
    order = get_object_or_404(Order, id=order_id)
    # Permitir pago si es cliente de la orden maestra o farmacia de la sub-orden
    if not (order.client.user == request.user or order.pharmacy.user == request.user):
        from django.http import Http404
        raise Http404("No tienes permiso para ver esta orden")

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

                # Si es una sub-orden, actualizar el estado de pago de la orden maestra
                if order.master_order:
                    # Verificar si todas las sub-órdenes están pagadas
                    all_sub_orders_paid = all(
                        sub_order.payment_status == 'completed'
                        for sub_order in order.master_order.sub_orders.all()
                    )
                    if all_sub_orders_paid:
                        order.master_order.payment_status = 'completed'
                        order.master_order.save()

                messages.success(request, 'Pago procesado exitosamente.')
                if order.master_order:
                    return redirect('orders:master_order_detail', master_order_id=order.master_order.id)
                else:
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
    # Permitir acceso tanto a clientes como a farmacias propietarias de la orden
    if request.user.user_type == 'client':
        order = get_object_or_404(Order, id=order_id, client__user=request.user)
        # Para clientes: mostrar opciones de pago y reseña
        can_review = (order.order_status == 'delivered' and not hasattr(order, 'review'))
        can_pay = (order.payment_status == 'pending' and order.order_status == 'pending')
        is_pharmacy_view = False
        is_client_view = True
        order_status_choices = []  # Clientes no pueden cambiar estado
    else:
        # Para farmacias, verificar que la orden pertenece a sus productos
        from users.models import PharmacyProfile
        pharmacy = get_object_or_404(PharmacyProfile, user=request.user)
        order = get_object_or_404(Order, id=order_id, pharmacy=pharmacy)
        # Para farmacias: mostrar opciones de gestión de entrega
        can_review = False
        can_pay = False
        is_pharmacy_view = True
        is_client_view = False
        # Todas las opciones de estado para farmacias
        order_status_choices = Order.ORDER_STATUS_CHOICES

    context = {
        'order': order,
        'can_review': can_review,
        'can_pay': can_pay,
        'is_pharmacy_view': is_pharmacy_view,
        'is_client_view': is_client_view,
        'order_status_choices': order_status_choices,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def master_order_list(request):
    """Lista de órdenes maestras del cliente"""
    client_profile = get_object_or_404(ClientProfile, user=request.user)
    master_orders = MasterOrder.objects.filter(client=client_profile).order_by('-created_at')

    return render(request, 'orders/master_order_list.html', {
        'master_orders': master_orders,
    })


@login_required
def master_order_detail(request, master_order_id):
    """Vista detallada de una orden maestra"""
    master_order = get_object_or_404(MasterOrder, id=master_order_id, client__user=request.user)
    sub_orders = master_order.sub_orders.all().prefetch_related('items__product', 'pharmacy')

    return render(request, 'orders/master_order_detail.html', {
        'master_order': master_order,
        'sub_orders': sub_orders,
    })


@login_required
def order_list(request):
    """Lista de órdenes del usuario"""
    from users.models import PharmacyProfile

    if request.user.user_type == 'client':
        # Para clientes, mostrar órdenes maestras
        return master_order_list(request)
    else:
        # Para farmacias, mostrar órdenes de sus productos
        pharmacy_profile = get_object_or_404(PharmacyProfile, user=request.user)
        orders = Order.objects.filter(pharmacy=pharmacy_profile).order_by('-created_at')
        is_client = False
        is_pharmacy = True

    context = {
        'orders': orders,
        'is_client': is_client,
        'is_pharmacy': is_pharmacy,
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def delivery_status(request, order_id):
    """Vista del estado de entrega"""
    order = get_object_or_404(Order, id=order_id, client__user=request.user)
    delivery = get_object_or_404(Delivery, order=order)

    return render(request, 'orders/delivery_status.html', {
        'order': order,
        'delivery': delivery,
    })


@pharmacy_required
def update_order_status(request, order_id):
    """Vista para que farmacias actualicen el estado de las órdenes"""

    from users.models import PharmacyProfile
    pharmacy = get_object_or_404(PharmacyProfile, user=request.user)
    order = get_object_or_404(Order, id=order_id, pharmacy=pharmacy)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Permitir todos los estados de ORDER_STATUS_CHOICES
        valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        if new_status in valid_statuses:
            # Si el estado seleccionado es el mismo que el actual
            if new_status == order.order_status:
                # Verificar si hay un estado siguiente lógico en el flujo
                status_flow = ['pending', 'paid', 'confirmed', 'preparing', 'ready_for_delivery', 'in_delivery', 'delivered', 'cancelled']
                current_index = status_flow.index(order.order_status) if order.order_status in status_flow else -1

                if current_index >= 0 and current_index < len(status_flow) - 1:
                    next_status = status_flow[current_index + 1]
                    # Solo permitir avanzar al siguiente estado lógico (excepto cancelled que es especial)
                    if next_status != 'cancelled':
                        new_status = next_status
                        messages.info(request, f'Actualizando automáticamente al siguiente estado: {Order.ORDER_STATUS_CHOICES[current_index + 1][1]}')
                    else:
                        messages.warning(request, f'La orden ya está en estado final: {order.get_order_status_display()}. No se puede avanzar más.')
                        return redirect('orders:order_detail', order_id=order.id)
                else:
                    messages.warning(request, f'La orden ya está en estado final: {order.get_order_status_display()}. No se puede actualizar más.')
                    return redirect('orders:order_detail', order_id=order.id)

            # Si la orden se confirma (pago confirmado), descontar stock automáticamente
            if new_status == 'confirmed' and order.order_status == 'paid':
                # Descontar stock de cada producto en la orden
                for item in order.items.all():
                    product = item.product
                    if product.stock_quantity >= item.quantity:
                        product.stock_quantity -= item.quantity
                        product.save()
                        messages.info(request, f'Stock actualizado: {product.name} (-{item.quantity})')
                    else:
                        messages.error(request, f'Stock insuficiente para {product.name}. Stock disponible: {product.stock_quantity}')
                        return redirect('orders:order_detail', order_id=order.id)

            order.order_status = new_status
            order.save()
            messages.success(request, f'Estado de la orden actualizado a: {order.get_order_status_display()}')
        else:
            messages.error(request, 'Estado no válido.')

    return redirect('orders:order_detail', order_id=order.id)


@pharmacy_required
def start_delivery(request, order_id):
    """Vista para iniciar el proceso de entrega"""

    from users.models import PharmacyProfile
    pharmacy = get_object_or_404(PharmacyProfile, user=request.user)
    order = get_object_or_404(Order, id=order_id, pharmacy=pharmacy)

    if request.method == 'POST' and order.order_status == 'ready_for_delivery':
        delivery_type = request.POST.get('delivery_type')
        external_service = request.POST.get('external_service')

        # Crear registro de entrega
        delivery = Delivery.objects.create(
            order=order,
            delivery_type=delivery_type,
            external_service=external_service if delivery_type == 'external' else None,
            status='assigned'
        )

        # Actualizar estado de la orden
        order.order_status = 'in_delivery'
        order.save()

        messages.success(request, f'Entrega iniciada vía {delivery.get_delivery_type_display()}')

    return redirect('orders:order_detail', order_id=order.id)
