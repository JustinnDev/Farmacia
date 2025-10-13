from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, PharmacyProfile, ClientProfile


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
    class Meta:
        model = PharmacyProfile
        fields = [
            'pharmacy_name', 'description', 'address', 'city', 'state', 'zip_code',
            'latitude', 'longitude', 'opening_time', 'closing_time', 'website', 'email'
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