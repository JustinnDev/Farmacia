from decimal import Decimal
from django.conf import settings
from products.models import Product


class Cart:
    """Clase para manejar el carrito de compras"""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """Agregar producto al carrito"""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.discounted_price),
                'pharmacy_id': product.pharmacy.id,
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        """Guardar el carrito en la sesión"""
        self.session.modified = True

    def remove(self, product):
        """Remover producto del carrito"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """Iterar sobre los items del carrito"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Contar items en el carrito"""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calcular precio total"""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_pharmacy(self):
        """Obtener la farmacia del carrito (todos los productos deben ser de la misma farmacia)"""
        if not self.cart:
            return None
        pharmacy_ids = set(item['pharmacy_id'] for item in self.cart.values())
        if len(pharmacy_ids) != 1:
            # Todos los productos deben ser de la misma farmacia
            raise ValueError("Todos los productos deben ser de la misma farmacia")
        from users.models import PharmacyProfile
        return PharmacyProfile.objects.get(id=list(pharmacy_ids)[0])

    def clear(self):
        """Limpiar el carrito"""
        del self.session[settings.CART_SESSION_ID]
        self.save()


# Configurar ID de sesión del carrito
if not hasattr(settings, 'CART_SESSION_ID'):
    settings.CART_SESSION_ID = 'cart'