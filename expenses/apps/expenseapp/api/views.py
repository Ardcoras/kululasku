from rest_framework import viewsets, permissions
from expenseapp.models import Organisation, ExpenseType, ExpenseLine
from .serializers import OrganisationSerializer, ExpenseTypeSerializer, ExpenseLineSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class OrganisationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        organisations = Organisation.objects.filter(active=True).order_by('name')
        org_ids = []

        person = getattr(self.request.user, 'person', None)
        person_type = getattr(person, 'type', None)

        for organisation in organisations:
            if person_type:
                types = ExpenseType.objects.filter(
                    organisation=organisation,
                    persontype=person_type,
                )
            else:
                types = ExpenseType.objects.filter(organisation=organisation)

            if types.exists():
                org_ids.append(organisation.id)

        return organisations.filter(id__in=org_ids)

class ExpenseTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpenseTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        qs = ExpenseType.objects.filter(active=True)
        if hasattr(user, 'person') and user.person.type:
            from django.db.models import Q
            qs = qs.filter(Q(persontype=user.person.type) | Q(persontype__isnull=True))
        return qs.order_by('organisation', 'name')

class PoolViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseLineSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        # The frontend expects unsubmitted pool items (expense=NULL)
        return ExpenseLine.objects.filter(user=self.request.user, expense__isnull=True).order_by('-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
