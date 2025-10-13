from django import forms
from .models import Order, Payment, Review


class OrderForm(forms.ModelForm):
    delivery_type = forms.ChoiceField(
        choices=[
            ('internal', 'Entrega Interna (Farmacia)'),
            ('external', 'Entrega Externa (Riddy/Yummy/Django)'),
            ('pickup', 'Recoger en Farmacia'),
        ],
        widget=forms.RadioSelect,
        label='Tipo de Entrega'
    )

    class Meta:
        model = Order
        fields = ['delivery_address', 'delivery_instructions']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dirección completa de entrega'}),
            'delivery_instructions': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Instrucciones adicionales (opcional)'}),
        }


class PaymentForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[
            ('c2p', 'Pago Móvil C2P (Convertir USD a VES usando tasa BCV)'),
            ('paypal', 'PayPal'),
            ('stripe', 'Stripe'),
            ('bank_transfer', 'Transferencia Bancaria'),
        ],
        widget=forms.RadioSelect,
        label='Método de Pago'
    )

    c2p_phone = forms.CharField(
        max_length=20,
        required=False,
        label='Número de Teléfono C2P',
        widget=forms.TextInput(attrs={'placeholder': '+58XXXXXXXXXX'})
    )

    c2p_reference = forms.CharField(
        max_length=100,
        required=False,
        label='Referencia C2P',
        widget=forms.TextInput(attrs={'placeholder': 'Referencia del pago'})
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')

        if payment_method == 'c2p':
            if not cleaned_data.get('c2p_phone'):
                raise forms.ValidationError('El número de teléfono C2P es requerido.')
            if not cleaned_data.get('c2p_reference'):
                raise forms.ValidationError('La referencia C2P es requerida.')

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} estrella{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Comparte tu experiencia...'}),
        }