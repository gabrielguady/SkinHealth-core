from rest_framework import routers
from core import viewsets


router = routers.DefaultRouter()

router.register(r'user', viewsets.UserViewSet)
router.register(r'patient', viewsets.PatientViewSet)
router.register(r'consultation', viewsets.ConsultationViewSet)
router.register(r'inspection', viewsets.VisualInspectionViewSet)
router.register(r'inspect_result', viewsets.AnalysisResultViewSet)

urlpatterns = router.urls