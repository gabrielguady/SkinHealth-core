from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from core import models, serializers, serializer_params, behaviors, filters


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    filterset_class = filters.UserFilter

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return [IsAuthenticated()]


class PatientViewSet(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = serializers.PatientSerializer
    filterset_class = filters.PatientFilter
    permission_classes = [IsAuthenticated]


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultation.objects.all()
    serializer_class = serializers.ConsultationSerializer
    filterset_class = filters.ConsultationFilter
    permission_classes = [IsAuthenticated]

    @action(methods=['POST'], detail=False, parser_classes=[MultiPartParser])
    def upload_file(self, request, *args, **kwargs):
        serializer = serializer_params.FileImageItemSerializerParam(data=request.data)
        serializer.is_valid(raise_exception=True)

        behavior = behaviors.MediaViewBehavior(**serializer.validated_data)
        response = behavior.run()

        return Response(data=response, status=status.HTTP_201_CREATED)


class ResultViewSet(viewsets.ModelViewSet):
    queryset = models.AnalysisResult.objects.all()
    serializer_class = serializers.ResultSerializer

class FileImageViewSet(viewsets.ModelViewSet):
    queryset = models.FileImageSkin.objects.all()
    serializer_class = serializers.FileImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()

        id_consultation = self.request.query_params.get('id_consultation')

        if id_consultation:
            if id_consultation:
                queryset = queryset.filter(consultation__id=id_consultation)
            else:
                queryset = queryset.none()

        return queryset
