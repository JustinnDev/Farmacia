from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'variant',
            'quantity', 'unit_price', 'total_price', 'prescription_image'
        ]
        read_only_fields = ['unit_price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.user.get_full_name', read_only=True)
    pharmacy_name = serializers.CharField(source='pharmacy.pharmacy_name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'order_status', 'payment_status',
            'subtotal', 'tax', 'delivery_fee', 'total',
            'delivery_type', 'delivery_address', 'delivery_instructions',
            'created_at', 'updated_at', 'payment_deadline', 'delivered_at',
            'client_notes', 'pharmacy_notes',
            'client_name', 'pharmacy_name', 'items'
        ]
        read_only_fields = [
            'order_number', 'payment_status', 'subtotal', 'tax',
            'delivery_fee', 'total', 'created_at', 'updated_at',
            'payment_deadline', 'delivered_at', 'client_name', 'pharmacy_name'
        ]

    def update(self, instance, validated_data):
        # Solo permitir actualizar order_status
        if 'order_status' in validated_data:
            new_status = validated_data['order_status']
            # Validar que el nuevo estado sea válido para confirmación
            if new_status not in ['confirmed', 'preparing', 'ready_for_delivery']:
                raise serializers.ValidationError("Estado de orden no válido para actualización")
            instance.order_status = new_status
            instance.save()
        return instance