from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('pharmacy', 'Farmacia'),
        ('client', 'Cliente'),
    )

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='client',
        verbose_name='Tipo de Usuario'
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número de teléfono debe estar en el formato: '+999999999'. Hasta 15 dígitos permitidos."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name='Número de Teléfono'
    )

    is_verified = models.BooleanField(default=False, verbose_name='Verificado')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client_profile')
    first_name = models.CharField(max_length=30, verbose_name='Nombre')
    last_name = models.CharField(max_length=30, verbose_name='Apellido')
    address = models.TextField(blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    state = models.CharField(max_length=100, blank=True, verbose_name='Estado')
    zip_code = models.CharField(max_length=10, blank=True, verbose_name='Código Postal')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Fecha de Nacimiento')

    class Meta:
        verbose_name = 'Perfil de Cliente'
        verbose_name_plural = 'Perfiles de Clientes'

    def __str__(self):
        return f"Perfil de {self.user.username}"


class PharmacyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='pharmacy_profile')
    pharmacy_name = models.CharField(max_length=200, verbose_name='Nombre de la Farmacia')
    description = models.TextField(blank=True, verbose_name='Descripción')
    address = models.TextField(verbose_name='Dirección')
    city = models.CharField(max_length=100, verbose_name='Ciudad')
    state = models.CharField(max_length=100, verbose_name='Estado')
    zip_code = models.CharField(max_length=10, verbose_name='Código Postal')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitud')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitud')
    google_maps_link = models.URLField(blank=True, verbose_name='Enlace de Google Maps')

    # Verification and reputation
    is_verified = models.BooleanField(default=False, verbose_name='Verificada')
    verification_documents = models.FileField(upload_to='verification_docs/', blank=True, null=True, verbose_name='Documentos de Verificación')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name='Calificación')
    total_reviews = models.PositiveIntegerField(default=0, verbose_name='Total de Reseñas')

    # Business hours
    opening_time = models.TimeField(null=True, blank=True, verbose_name='Hora de Apertura')
    closing_time = models.TimeField(null=True, blank=True, verbose_name='Hora de Cierre')

    # Contact
    website = models.URLField(blank=True, verbose_name='Sitio Web')
    email = models.EmailField(blank=True, verbose_name='Correo Electrónico')

    class Meta:
        verbose_name = 'Perfil de Farmacia'
        verbose_name_plural = 'Perfiles de Farmacias'

    def __str__(self):
        return self.pharmacy_name

    def update_rating(self):
        """Update pharmacy rating based on reviews"""
        from orders.models import Review
        reviews = Review.objects.filter(pharmacy=self)
        if reviews.exists():
            self.rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.total_reviews = reviews.count()
            self.save()
