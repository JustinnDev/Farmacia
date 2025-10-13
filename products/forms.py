from django import forms
from .models import Product, Category, ProductImage, ProductVariant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'brand', 'price',
            'original_price', 'stock_quantity', 'requires_prescription',
            'main_image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'original_price': forms.NumberInput(attrs={'step': '0.01'}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'sku_variant', 'price_modifier', 'stock_quantity']
        widgets = {
            'price_modifier': forms.NumberInput(attrs={'step': '0.01'}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']


ProductVariantFormSet = forms.inlineformset_factory(
    Product, ProductVariant, form=ProductVariantForm,
    extra=1, can_delete=True, can_delete_extra=True
)

ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage, form=ProductImageForm,
    extra=1, can_delete=True, can_delete_extra=True
)