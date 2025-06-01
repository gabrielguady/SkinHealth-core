from django.shortcuts import render

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer # Importe seu serializador customizado

class MyTokenObtainPairView(TokenObtainPairView):
    """
    View customizada que usa MyTokenObtainPairSerializer.
    """
    serializer_class = MyTokenObtainPairSerializer
