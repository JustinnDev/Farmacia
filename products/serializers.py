from rest_framework import serializers
from .models import Product, Category, ProductImage, ProductVariant

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    additional_images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'sku', 'price', 'original_price',
            'discount_percentage', 'stock_quantity', 'requires_prescription',
            'main_image', 'category', 'additional_images', 'variants', 'is_active'
        ]
        read_only_fields = ['pharmacy', 'sku']  # El SKU se auto-genera, pharmacy se asigna automáticamente

    def create(self, validated_data):
        # Asigna la farmacia del usuario autenticado
        validated_data['pharmacy'] = self.context['request'].user.pharmacy_profile
        return super().create(validated_data)