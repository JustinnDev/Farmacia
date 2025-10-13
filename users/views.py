from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import CustomUser, PharmacyProfile, ClientProfile
from .forms import UserRegistrationForm, PharmacyProfileForm, ClientProfileForm


def home(request):
    """Vista de la página principal"""
    return render(request, 'users/home.html')


def register(request):
    """Vista de registro de usuarios"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro exitoso. Bienvenido a FarmaYa!')
            return redirect('users:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Vista de inicio de sesión"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido de vuelta, {user.username}!')
            return redirect('users:home')
        else:
            messages.error(request, 'Credenciales inválidas.')
    return render(request, 'users/login.html')


def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('users:home')


@login_required
def profile(request):
    """Vista del perfil del usuario"""
    user = request.user

    if user.user_type == 'pharmacy':
        profile, created = PharmacyProfile.objects.get_or_create(user=user)
        if request.method == 'POST':
            form = PharmacyProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('users:profile')
        else:
            form = PharmacyProfileForm(instance=profile)
        return render(request, 'users/pharmacy_profile.html', {'profile': profile, 'form': form})

    else:  # client
        profile, created = ClientProfile.objects.get_or_create(user=user)
        if request.method == 'POST':
            form = ClientProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('users:profile')
        else:
            form = ClientProfileForm(instance=profile)
        return render(request, 'users/client_profile.html', {'profile': profile, 'form': form})


def pharmacy_detail(request, pharmacy_id):
    """Vista detallada de una farmacia (landing page)"""
    pharmacy = get_object_or_404(PharmacyProfile, id=pharmacy_id)
    products = pharmacy.products.filter(is_active=True)[:12]  # Mostrar primeros 12 productos

    context = {
        'pharmacy': pharmacy,
        'products': products,
        'total_products': pharmacy.products.filter(is_active=True).count(),
    }
    return render(request, 'users/pharmacy_detail.html', context)
