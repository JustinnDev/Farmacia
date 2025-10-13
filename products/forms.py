from django import forms
from .models import Product, Category, ProductImage, ProductVariant


class ProductForm(forms.ModelForm):
    sku = forms.CharField(
        required=False,
        label='SKU',
        help_text='Deja vacío para generar automáticamente',
        widget=forms.TextInput(attrs={'placeholder': 'Se generará automáticamente'})
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'brand', 'sku', 'price',
            'original_price', 'stock_quantity', 'requires_prescription',
            'main_image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Precio en USD'}),
            'original_price': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Precio original en USD'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer SKU opcional en el formulario
        self.fields['sku'].required = False


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