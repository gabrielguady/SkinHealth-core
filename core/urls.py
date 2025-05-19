from rest_framework import routers
from core import viewsets


router = routers.DefaultRouter()

router.register('user', viewsets.UserViewSet)
router.register('patient', viewsets.PatientViewSet)
router.register('consultation', viewsets.ConsultationViewSet)
router.register('result', viewsets.ResultViewSet)
router.register('file_image', viewsets.FileImageViewSet)

urlpatterns = router.urls