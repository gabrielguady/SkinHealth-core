from django.urls import path, include
from rest_framework_nested import routers
from core import viewsets

# Router principal para endpoints de nível superior
router = routers.DefaultRouter()
router.register(r'users', viewsets.UserViewSet)
router.register(r'patients', viewsets.PatientViewSet)

# Router aninhado para consultas dentro de pacientes
patients_router = routers.NestedSimpleRouter(router, r'patients', lookup='patient')
patients_router.register(r'consultations', viewsets.ConsultationViewSet, basename='patient-consultations')

# Router aninhado para imagens dentro de consultas
consultations_router = routers.NestedSimpleRouter(patients_router, r'consultations', lookup='consultation')
consultations_router.register(r'images', viewsets.FileImageViewSet, basename='consultation-images')

# Router aninhado para resultados de análise dentro de imagens
images_router = routers.NestedSimpleRouter(consultations_router, r'images', lookup='fileimageskin')
images_router.register(r'results', viewsets.ResultViewSet, basename='image-results')

# Crie uma lista com todos os URLs gerados pelos routers
# Isso é mais robusto do que desempacotar diretamente dentro de urlpatterns
router_urls = []
router_urls.extend(router.urls)
router_urls.extend(patients_router.urls)
router_urls.extend(consultations_router.urls)
router_urls.extend(images_router.urls)

# Inclua a lista consolidada de URLs em urlpatterns
urlpatterns = [
    path('', include(router_urls)),
]