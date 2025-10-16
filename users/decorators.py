from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def pharmacy_required(view_func):
    """
    Decorador que requiere que el usuario esté autenticado y sea de tipo 'pharmacy'.
    Si no cumple, redirige al perfil con un mensaje de error.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'pharmacy':
            messages.error(request, 'Esta página es solo para farmacias.')
            print("--------------------------------")
            return redirect('users:profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view