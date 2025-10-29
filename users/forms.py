from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, PharmacyProfile, ClientProfile
from .utils import extract_coords


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label='Tipo de Usuario'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user


class PharmacyProfileForm(forms.ModelForm):
    def clean_google_maps_link(self):
        google_maps_link = self.cleaned_data.get('google_maps_link')
        if google_maps_link:
            if not google_maps_link.startswith('https://www.google.com/maps/'):
                raise ValidationError('El enlace debe ser una URL válida de Google Maps.')
        return google_maps_link

    def save(self, commit=True):
        instance = super().save(commit=False)
        google_maps_link = self.cleaned_data.get('google_maps_link')
        if google_maps_link:
            coords = extract_coords(google_maps_link)
            if coords:
                instance.latitude = coords[0]
                instance.longitude = coords[1]
        if commit:
            instance.save()
        return instance

    class Meta:
        model = PharmacyProfile
        fields = [
            'pharmacy_name', 'description', 'address', 'city', 'state', 'zip_code',
            'latitude', 'longitude', 'google_maps_link', 'opening_time', 'closing_time', 'website', 'email'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'opening_time': forms.TimeInput(attrs={'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ['first_name', 'last_name', 'address', 'city', 'state', 'zip_code', 'date_of_birth']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }