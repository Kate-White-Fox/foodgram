from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class TokenLoginView(APIView):
    """
    Логин, возвращающий только {"auth_token": "..."}
    """
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'email и password обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {'error': 'Неверные учетные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


class TokenLogoutView(APIView):
    """Удаление токена (логаут) — возвращает 204"""
    permission_classes = []

    def post(self, request):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                from rest_framework.authtoken.models import Token
                token = Token.objects.get(key=token_key)
                token.delete()
            except Token.DoesNotExist:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)
