from django.db import models
from django.conf import settings
from users.models import CustomUser, PharmacyProfile, ClientProfile
from products.models import Product, ProductVariant


class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'Preparando'),
        ('ready_for_delivery', 'Listo para Entrega'),
        ('in_delivery', 'En Entrega'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    )

    # Relationships
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='orders', verbose_name='Cliente')
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.CASCADE, related_name='orders', verbose_name='Farmacia')

    # Order details
    order_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Orden')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending', verbose_name='Estado de la Orden')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='Estado del Pago')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal (USD)')
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Impuestos (USD)')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Costo de Entrega (USD)')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total (USD)')

    # Delivery information
    delivery_type = models.CharField(max_length=20, choices=[
        ('internal', 'Entrega Interna'),
        ('external', 'Entrega Externa'),
        ('pickup', 'Recoger en Farmacia'),
    ], verbose_name='Tipo de Entrega')

    delivery_address = models.TextField(blank=True, verbose_name='Dirección de Entrega')
    delivery_instructions = models.TextField(blank=True, verbose_name='Instrucciones de Entrega')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    payment_deadline = models.DateTimeField(verbose_name='Fecha Límite de Pago')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Entregado el')

    # Notes
    client_notes = models.TextField(blank=True, verbose_name='Notas del Cliente')
    pharmacy_notes = models.TextField(blank=True, verbose_name='Notas de la Farmacia')

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Orden {self.order_number} - {self.client.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Orden')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Producto')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Variante')

    quantity = models.PositiveIntegerField(verbose_name='Cantidad')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio Unitario')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio Total')

    # Prescription info if required
    prescription_image = models.ImageField(upload_to='prescriptions/', null=True, blank=True, verbose_name='Imagen de Receta')

    class Meta:
        verbose_name = 'Artículo de Orden'
        verbose_name_plural = 'Artículos de Órdenes'

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('c2p', 'Pago Móvil C2P'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Transferencia Bancaria'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', verbose_name='Orden')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='Método de Pago')

    # C2P specific fields
    c2p_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono C2P')
    c2p_reference = models.CharField(max_length=100, blank=True, verbose_name='Referencia C2P')

    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto (USD)')
    currency = models.CharField(max_length=3, default='USD', verbose_name='Moneda')
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name='ID de Transacción')
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Pago')

    # Status
    is_successful = models.BooleanField(default=False, verbose_name='Pago Exitoso')

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago de {self.order.order_number}"


class Delivery(models.Model):
    DELIVERY_STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('assigned', 'Asignado'),
        ('picked_up', 'Recogido'),
        ('in_transit', 'En Tránsito'),
        ('delivered', 'Entregado'),
        ('failed', 'Fallido'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery', verbose_name='Orden')

    # Delivery details
    delivery_type = models.CharField(max_length=20, choices=[
        ('internal', 'Entrega Interna'),
        ('external', 'Entrega Externa'),
        ('pickup', 'Recoger en Farmacia'),
    ], verbose_name='Tipo de Entrega')

    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending', verbose_name='Estado')

    # External delivery service info
    external_service = models.CharField(max_length=50, blank=True, choices=[
        ('riddy', 'Riddy'),
        ('yummy', 'Yummy'),
        ('django_delivery', 'Django Delivery'),
    ], verbose_name='Servicio Externo')

    tracking_number = models.CharField(max_length=100, blank=True, verbose_name='Número de Seguimiento')
    estimated_delivery_time = models.DateTimeField(null=True, blank=True, verbose_name='Tiempo Estimado de Entrega')

    # Delivery personnel
    delivery_person_name = models.CharField(max_length=100, blank=True, verbose_name='Nombre del Repartidor')
    delivery_person_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono del Repartidor')

    # Timestamps
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Asignado el')
    picked_up_at = models.DateTimeField(null=True, blank=True, verbose_name='Recogido el')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Entregado el')

    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'

    def __str__(self):
        return f"Entrega de {self.order.order_number}"


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review', verbose_name='Orden')
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='reviews', verbose_name='Cliente')
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.CASCADE, related_name='reviews', verbose_name='Farmacia')

    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Calificación')
    comment = models.TextField(blank=True, verbose_name='Comentario')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reseña de {self.client.user.username} para {self.pharmacy.pharmacy_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update pharmacy rating
        self.pharmacy.update_rating()
