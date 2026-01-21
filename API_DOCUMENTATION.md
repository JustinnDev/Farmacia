# Documentación de la API para Farmacias

Esta API permite a las farmacias gestionar su inventario y confirmar órdenes externamente desde sus sistemas ERP, sin necesidad de usar la interfaz web.

## Acceso a la Documentación Web

Las farmacias pueden acceder a esta documentación desde su panel de control en la aplicación web:
- Ve a tu Dashboard de Farmacia
- Busca la sección "Documentación API" o "Integración ERP"
- URL directa: `/users/pharmacy/api-docs/`

Esta página web incluye ejemplos interactivos y tu token de API personal.

## Verificar Estado de la API

### Health Check

**Endpoint:** `GET /api/health/`

**Descripción:** Verifica que la API esté funcionando correctamente. No requiere autenticación.

**Respuesta:**
```json
{
    "status": "ok",
    "message": "FarmaYa API is running",
    "timestamp": "2024-01-16T18:43:00.000000Z",
    "version": "1.0.0"
}
```

**Ejemplo con cURL:**
```bash
curl https://tu-dominio.com/api/health/
```

## Autenticación

La API utiliza autenticación por tokens. Las farmacias pueden obtener su token de dos formas:

### Opción 1: Desde la Interfaz Web

1. Inicia sesión como farmacia
2. Ve a **Dashboard → Documentación API**
3. Tu token aparecerá en la sección "Tu Token de API"
4. Copia el token para usar en tus integraciones

### Opción 2: Desde la API

**Endpoint:** `POST /api/auth/login/`

**Cuerpo de la petición:**
```json
{
    "username": "usuario_farmacia",
    "password": "contraseña"
}
```

**Respuesta:**
```json
{
    "token": "abc123def456...",
    "user_id": 1,
    "username": "usuario_farmacia",
    "user_type": "pharmacy"
}
```

Para autenticar las siguientes peticiones, incluir el header:
```
Authorization: Token abc123def456...
```

## Endpoints de Productos

### Listar Productos

**Endpoint:** `GET /api/products/`

**Descripción:** Lista todos los productos de la farmacia autenticada.

**Headers requeridos:**
```
Authorization: Token TU_TOKEN
Accept: application/json
```

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Paracetamol 500mg",
        "sku": "FAR-500MG-ABC123",
        "price": "5.99",
        "stock_quantity": 100,
        "is_active": true,
        ...
    }
]
```

### Crear Producto

**Endpoint:** `POST /api/products/`

**Cuerpo de la petición:**
```json
{
    "name": "Nuevo Producto",
    "description": "Descripción del producto",
    "price": "10.50",
    "stock_quantity": 50,
    "requires_prescription": false,
    "main_image": "url_de_la_imagen"
}
```

**Nota:** El SKU se genera automáticamente.

### Actualizar Producto

**Endpoint:** `PUT /api/products/{id}/`

**Cuerpo de la petición:**
```json
{
    "stock_quantity": 75,
    "price": "11.00"
}
```

### Eliminar Producto

**Endpoint:** `DELETE /api/products/{id}/`

## Endpoints de Órdenes

### Listar Órdenes

**Endpoint:** `GET /api/orders/`

**Descripción:** Lista todas las órdenes de la farmacia autenticada.

**Respuesta:**
```json
[
    {
        "id": 1,
        "order_number": "ORD-ABC123",
        "order_status": "paid",
        "client_name": "Juan Pérez",
        "total": "25.99",
        "items": [
            {
                "product_name": "Paracetamol 500mg",
                "quantity": 2,
                "unit_price": "5.99"
            }
        ]
    }
]
```

### Confirmar Orden

**Endpoint:** `PATCH /api/orders/{id}/confirm/`

**Descripción:** Confirma una orden pagada y descuenta automáticamente el stock.

**Respuesta:**
```json
{
    "id": 1,
    "order_number": "ORD-ABC123",
    "order_status": "confirmed",
    ...
}
```

### Actualizar Estado de Orden

**Endpoint:** `PATCH /api/orders/{id}/`

**Cuerpo de la petición:**
```json
{
    "order_status": "preparing"
}
```

**Estados válidos:** `confirmed`, `preparing`, `ready_for_delivery`

## Códigos de Error

- `400 Bad Request`: Datos inválidos o acción no permitida
- `401 Unauthorized`: Token inválido o faltante
- `403 Forbidden`: No tienes permisos para este recurso
- `404 Not Found`: Recurso no encontrado

## Notas Importantes

1. **Permisos:** Solo las farmacias pueden acceder a sus propios productos y órdenes.
2. **Stock:** Al confirmar una orden, el stock se descuenta automáticamente.
3. **Imágenes:** Las URLs de imágenes deben ser accesibles públicamente.
4. **Validaciones:** Los productos requieren nombre, precio y cantidad en stock.
5. **Seguridad:** Todas las peticiones deben incluir el token de autenticación.

## Ejemplo de Integración con ERP

```python
import requests

# Obtener token
auth_response = requests.post('https://tu-dominio.com/api/auth/login/', json={
    'username': 'farmacia_user',
    'password': 'password123'
})
token = auth_response.json()['token']

headers = {'Authorization': f'Token {token}'}

# Actualizar stock de producto
requests.put('https://tu-dominio.com/api/products/1/', json={
    'stock_quantity': 50
}, headers=headers)

# Confirmar orden
requests.patch('https://tu-dominio.com/api/orders/1/confirm/', headers=headers)