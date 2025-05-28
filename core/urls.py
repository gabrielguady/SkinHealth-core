from django.urls import path, include
from rest_framework import routers
from .viewsets import (
    UserViewSet,
    PatientViewSet,
    ConsultationViewSet,
    AnalysisResultViewSet,
    FileImageSkinViewSet
)


router = routers.DefaultRouter()

router.register('user', UserViewSet) # /api/skin/user/
router.register('patient', PatientViewSet) # /api/skin/patient/
router.register('consultation', ConsultationViewSet) # /api/skin/consultation/
router.register('analysis_result', AnalysisResultViewSet) # /api/skin/analysis_result/
router.register('file_image', FileImageSkinViewSet) # /api/skin/file_image/

urlpatterns = router.urls