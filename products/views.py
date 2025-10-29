from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import inlineformset_factory
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from .models import Product, Category
from .forms import ProductForm, ProductVariantFormSet, ProductImageFormSet
from users.models import PharmacyProfile
from users.decorators import pharmacy_required
from users.utils import calculate_distance


def product_list(request, category_slug=None):
    """Vista de lista de productos con filtros opcionales"""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0)

    # Filtrar por categoría si se especifica
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Filtros adicionales
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query)
        )

    # Filtro por ubicación
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    max_distance = request.GET.get('distance', 10)  # Default 10km

    print("-----------------")
    print(max_distance)

    if user_lat and user_lng:
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            max_distance = float(max_distance)
            print(f"user {user_lat} {user_lng}")

            # Filter pharmacies within the specified distance
            nearby_pharmacies = []
            for pharmacy in PharmacyProfile.objects.filter(latitude__isnull=False, longitude__isnull=False):
                distance = calculate_distance(user_lat, user_lng, pharmacy.latitude, pharmacy.longitude)
                print(f"{pharmacy.pharmacy_name} : {distance}")
                if distance <= max_distance:
                    nearby_pharmacies.append(pharmacy.id)

            products = products.filter(pharmacy_id__in=nearby_pharmacies)
        except (ValueError, TypeError):
            pass  # Ignore invalid coordinates



    # Ordenamiento
    sort_by = request.GET.get('sort', 'name')

    print(sort_by)

    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-pharmacy__rating')
    else:
        products = products.order_by('name')

    # Paginación
    paginator = Paginator(products, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Variables calculadas para el template
    is_client = request.user.is_authenticated and request.user.user_type == 'client'
    is_pharmacy = request.user.is_authenticated and request.user.user_type == 'pharmacy'

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'is_client': is_client,
        'is_pharmacy': is_pharmacy,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'max_distance': max_distance,
    }
    return render(request, 'products/product_list.html', context)


def product_search(request):
    """Vista de búsqueda de productos"""
    query = request.GET.get('q', '')
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(pharmacy__pharmacy_name__icontains=query)
        )

    # Ordenamiento
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-pharmacy__rating')
    else:
        products = products.order_by('name')

    # Paginación
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Variables calculadas para el template
    is_client = request.user.is_authenticated and request.user.user_type == 'client'
    is_pharmacy = request.user.is_authenticated and request.user.user_type == 'pharmacy'

    context = {
        'page_obj': page_obj,
        'query': query,
        'search_query': query,  # Para mantener consistencia con product_list
        'search_results': True,
        'categories': categories,
        'sort_by': sort_by,
        'is_client': is_client,
        'is_pharmacy': is_pharmacy,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, product_id):
    """Vista detallada de un producto"""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # Productos relacionados (misma categoría o misma farmacia)
    related_products = Product.objects.filter(
        Q(category=product.category) | Q(pharmacy=product.pharmacy)
    ).exclude(id=product.id).filter(is_active=True, stock_quantity__gt=0)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)


@pharmacy_required
def product_create(request):
    """Vista para crear un nuevo producto (solo farmacias)"""

    pharmacy = get_object_or_404(PharmacyProfile, user=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        variant_formset = ProductVariantFormSet(request.POST, prefix='variants')
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')

        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            product = form.save(commit=False)
            product.pharmacy = pharmacy
            product.save()

            # Guardar variantes
            variants = variant_formset.save(commit=False)
            for variant in variants:
                variant.product = product
                variant.save()

            # Guardar imágenes
            images = image_formset.save(commit=False)
            for image in images:
                image.product = product
                image.save()

            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('products:product_detail', product_id=product.id)
    else:
        form = ProductForm()
        variant_formset = ProductVariantFormSet(prefix='variants')
        image_formset = ProductImageFormSet(prefix='images')

    context = {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'is_create': True,
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_update(request, product_id):
    """Vista para editar un producto (solo el propietario)"""
    product = get_object_or_404(Product, id=product_id, pharmacy__user=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        variant_formset = ProductVariantFormSet(request.POST, prefix='variants', instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images', instance=product)

        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            form.save()
            variant_formset.save()
            image_formset.save()

            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('products:product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
        variant_formset = ProductVariantFormSet(prefix='variants', instance=product)
        image_formset = ProductImageFormSet(prefix='images', instance=product)

    context = {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'product': product,
        'is_create': False,
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, product_id):
    """Vista para eliminar un producto (solo el propietario)"""
    product = get_object_or_404(Product, id=product_id, pharmacy__user=request.user)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
        return redirect('users:profile')

    context = {
        'product': product,
    }
    return render(request, 'products/product_confirm_delete.html', context)


@pharmacy_required
def pharmacy_products(request):
    """Vista para que las farmacias vean y gestionen sus productos"""

    pharmacy = get_object_or_404(PharmacyProfile, user=request.user)
    products = Product.objects.filter(pharmacy=pharmacy).order_by('-created_at')

    # Estadísticas para el template
    active_products = pharmacy.products.filter(is_active=True).count()
    low_stock_products = pharmacy.products.filter(stock_quantity__lte=10, is_active=True).count()
    prescription_products = pharmacy.products.filter(requires_prescription=True, is_active=True).count()
    empty_stock_products = pharmacy.products.filter(stock_quantity=0, is_active=True).count()

    # Paginación
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'pharmacy': pharmacy,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'prescription_products': prescription_products,
        'empty_stock_products' : empty_stock_products,
    }

    return render(request, 'products/pharmacy_products.html', context)


@require_GET
@cache_page(60 * 15)  # Cache por 15 minutos
def autocomplete(request):
    """Endpoint API para autocompletado de productos - solo nombres para completar la búsqueda"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    # Buscar nombres de productos únicos que coincidan con la query
    product_names = Product.objects.filter(
        Q(is_active=True) &
        Q(stock_quantity__gt=0) &
        Q(name__icontains=query)
    ).values_list('name', flat=True).distinct()[:8]  # Máximo 8 resultados únicos

    results = []
    for name in product_names:
        results.append({
            'name': name,
        })

    return JsonResponse({'results': results})
