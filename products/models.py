from django.db import models
from django.conf import settings
from users.models import PharmacyProfile


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Imagen')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.name


class Product(models.Model):
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.CASCADE, related_name='products', verbose_name='Farmacia')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='Categoría')

    name = models.CharField(max_length=200, verbose_name='Nombre del Producto')
    description = models.TextField(blank=True, verbose_name='Descripción')
    brand = models.CharField(max_length=100, blank=True, verbose_name='Marca')
    sku = models.CharField(max_length=100, unique=True, verbose_name='SKU')

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio (USD)')
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Precio Original (USD)')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Descuento (%)')

    # Stock and availability
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='Cantidad en Stock')
    is_available = models.BooleanField(default=True, verbose_name='Disponible')
    requires_prescription = models.BooleanField(default=False, verbose_name='Requiere Receta')

    # Images
    main_image = models.ImageField(upload_to='products/', verbose_name='Imagen Principal')
    additional_images = models.ManyToManyField('ProductImage', blank=True, related_name='products', verbose_name='Imágenes Adicionales')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.pharmacy.pharmacy_name}"

    @property
    def discounted_price(self):
        if self.discount_percentage > 0:
            return self.price * (1 - self.discount_percentage / 100)
        return self.price

    @property
    def is_on_sale(self):
        return self.discount_percentage > 0

    def save(self, *args, **kwargs):
        if self.original_price and self.original_price > self.price:
            self.discount_percentage = ((self.original_price - self.price) / self.original_price) * 100

        # Auto-generar SKU si no está establecido
        if not self.sku:
            import uuid
            # Generar SKU único basado en farmacia y nombre del producto
            base_sku = f"{self.pharmacy.pharmacy_name[:3].upper()}-{self.name[:10].replace(' ', '-').upper()}"
            # Agregar sufijo único para evitar colisiones
            unique_suffix = str(uuid.uuid4())[:8].upper()
            self.sku = f"{base_sku}-{unique_suffix}"

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Producto')
    image = models.ImageField(upload_to='products/additional/', verbose_name='Imagen')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Texto Alternativo')
    order = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        ordering = ['order']

    def __str__(self):
        return f"Imagen de {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='Producto')
    name = models.CharField(max_length=100, verbose_name='Nombre de Variante')  # e.g., "500mg", "10ml"
    sku_variant = models.CharField(max_length=100, unique=True, verbose_name='SKU de Variante')
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Modificador de Precio')
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='Cantidad en Stock')

    class Meta:
        verbose_name = 'Variante de Producto'
        verbose_name_plural = 'Variantes de Productos'

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def final_price(self):
        return self.product.price + self.price_modifier
