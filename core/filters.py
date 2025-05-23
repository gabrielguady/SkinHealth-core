from django_filters import filterset
from django_filters import rest_framework as filters

from core import models, choices

class UserFilter(filterset.FilterSet):
    professional_id = filters.CharFilter(lookup_expr=choices.LIKE)
    username = filters.CharFilter(lookup_expr=choices.LIKE)
    class Meta:
        model = models.User
        fields = ['professional_id', 'username']

class PatientFilter(filterset.FilterSet):
    name = filters.CharFilter(lookup_expr=choices.LIKE)
    date_of_birth = filters.DateFilter(lookup_expr=choices.ICONTAINS)
    gender = filters.CharFilter(lookup_expr=choices.LIKE)
    cellphone = filters.CharFilter(lookup_expr=choices.LIKE)
    cpf = filters.CharFilter(lookup_expr=choices.LIKE)
    email = filters.CharFilter(lookup_expr=choices.LIKE)

    class Meta:
        model = models.Patient
        fields = ['name', 'date_of_birth', 'gender', 'cellphone', 'cpf', 'email']

class ConsultationFilter(filterset.FilterSet):
    agent = filters.CharFilter(lookup_expr=choices.LIKE)
    patient = filters.CharFilter(field_name='patient__name', lookup_expr=choices.LIKE)
    date_consultation = filters.DateFilter(lookup_expr=choices.ICONTAINS)
    notes = filters.CharFilter(lookup_expr=choices.LIKE)

    class Meta:
        model = models.Consultation
        fields = ['agent', 'patient', 'date_consultation', 'notes']