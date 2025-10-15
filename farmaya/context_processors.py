def user_type(request):
    """Context processor para agregar el tipo de usuario al contexto"""
    if request.user.is_authenticated:
        return {'user_type': request.user.user_type}
    return {}


def pharmacy_context(request):
    """Context processor para datos específicos de farmacias"""
    if request.user.is_authenticated and request.user.user_type == 'pharmacy':
        from users.models import PharmacyProfile
        try:
            pharmacy = PharmacyProfile.objects.get(user=request.user)
            # Órdenes pendientes de confirmación
            pending_orders_count = pharmacy.orders.filter(order_status='paid').count()
            # Productos con stock bajo
            low_stock_count = pharmacy.products.filter(stock_quantity__lte=10, is_active=True).count()

            return {
                'pending_orders_count': pending_orders_count,
                'low_stock_count': low_stock_count,
            }
        except PharmacyProfile.DoesNotExist:
            pass
    return {}