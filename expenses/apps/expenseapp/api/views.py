from rest_framework import viewsets, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import PermissionDenied
from expenseapp.models import Organisation, ExpenseType, ExpenseLine
from .serializers import OrganisationSerializer, ExpenseTypeSerializer, ExpenseLineSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.throttling import ScopedRateThrottle
from django.db.models import Exists, OuterRef, Q


class ThrottledObtainAuthToken(ObtainAuthToken):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'api_login'


class OrganisationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        person = getattr(self.request.user, 'person', None)
        person_type = getattr(person, 'type', None)

        type_filter = Q(organisation_id=OuterRef('pk'), active=True)
        if person_type:
            type_filter &= Q(persontype=person_type) | Q(persontype__isnull=True)

        types_qs = ExpenseType.objects.filter(type_filter)

        return Organisation.objects.filter(active=True).annotate(
            has_allowed_types=Exists(types_qs)
        ).filter(has_allowed_types=True).order_by('name')


class ExpenseTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpenseTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ExpenseType.objects.filter(active=True, organisation__active=True)
        if hasattr(user, 'person') and user.person.type:
            qs = qs.filter(Q(persontype=user.person.type) | Q(persontype__isnull=True))
        return qs.order_by('organisation', 'name')


def _assert_org_allowed(user, organisation_id):
    """
    Raises PermissionDenied if the user has no accessible expense types
    for the given organisation.
    """
    person = getattr(user, 'person', None)
    person_type = getattr(person, 'type', None)

    qs = ExpenseType.objects.filter(organisation_id=organisation_id, organisation__active=True, active=True)
    if person_type:
        qs = qs.filter(Q(persontype=person_type) | Q(persontype__isnull=True))

    if not qs.exists():
        raise PermissionDenied('You do not have access to the specified organisation.')


class PoolViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseLineSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        # The frontend expects unsubmitted pool items (expense=NULL)
        return ExpenseLine.objects.filter(user=self.request.user, expense__isnull=True).order_by('-id')

    def perform_create(self, serializer):
        organisation = serializer.validated_data.get('organisation')
        if organisation:
            _assert_org_allowed(self.request.user, organisation.id)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        organisation = serializer.validated_data.get('organisation')
        if organisation:
            _assert_org_allowed(self.request.user, organisation.id)
        serializer.save(user=self.request.user)
