from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category


def product_list(request, category_slug=None):
    """Vista de lista de productos con filtros opcionales"""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

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
    paginator = Paginator(products, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'products/product_list.html', context)


def product_search(request):
    """Vista de búsqueda de productos"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(pharmacy__pharmacy_name__icontains=query)
        )

    # Paginación
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'search_results': True,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, product_id):
    """Vista detallada de un producto"""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # Productos relacionados (misma categoría o misma farmacia)
    related_products = Product.objects.filter(
        Q(category=product.category) | Q(pharmacy=product.pharmacy)
    ).exclude(id=product.id).filter(is_active=True)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)
