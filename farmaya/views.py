from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de health check para verificar que la API esté funcionando.
    No requiere autenticación.
    """
    return Response({
        'status': 'ok',
        'message': 'FarmaYa API is running',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):
    """
    Custom auth token endpoint that's CSRF exempt.
    Returns token for authenticated users.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if username and password:
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username,
                    'user_type': user.user_type
                })
            else:
                return Response({'error': 'User account is disabled'}, status=400)
        else:
            return Response({'error': 'Invalid credentials'}, status=400)
    else:
        return Response({'error': 'Must include username and password'}, status=400)