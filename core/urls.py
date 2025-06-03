from rest_framework import routers
from core import viewsets

router = routers.DefaultRouter()

router.register('user', viewsets.UserViewSet) # /api/skin/user/
router.register('patient', viewsets.PatientViewSet) # /api/skin/patient/
router.register('consultation', viewsets.ConsultationViewSet) # /api/skin/consultation/
router.register('analysis_result', viewsets.AnalysisResultViewSet) # /api/skin/analysis_result/
router.register('file_image',viewsets.FileImageSkinViewSet) # /api/skin/file_image/

urlpatterns = router.urls