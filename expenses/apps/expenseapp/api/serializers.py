from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from expenseapp.models import Organisation, ExpenseType, ExpenseLine

class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ['id', 'name', 'business_id', 'active']

class ExpenseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseType
        fields = [
            'id', 'name', 'type', 'requires_receipt', 'multiplier', 
            'requires_endtime', 'requires_start_time', 'persontype', 
            'unit', 'organisation'
        ]

class ExpenseLineSerializer(serializers.ModelSerializer):
    receipt = serializers.FileField(required=False, allow_null=True, use_url=False)

    class Meta:
        model = ExpenseLine
        fields = [
            'id', 'description', 'begin_at', 'ended_at', 'expensetype',
            'accountdimension', 'basis', 'receipt', 'expense', 
            'user', 'organisation'
        ]
        read_only_fields = ['expense', 'user']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context['request'].user
        instance = self.instance

        organisation = attrs.get('organisation') or getattr(instance, 'organisation', None)
        expensetype = attrs.get('expensetype') or getattr(instance, 'expensetype', None)
        accountdimension = attrs.get('accountdimension') or getattr(instance, 'accountdimension', None)
        if 'receipt' in attrs:
            receipt = attrs['receipt']
        else:
            receipt = getattr(instance, 'receipt', None)
        ended_at = attrs.get('ended_at') or getattr(instance, 'ended_at', None)

        if not organisation:
            raise serializers.ValidationError({'organisation': 'This field is required.'})
        if not organisation.active:
            raise serializers.ValidationError({'organisation': 'Organisation is not active.'})

        if not expensetype:
            raise serializers.ValidationError({'expensetype': 'This field is required.'})
        if not expensetype.active:
            raise serializers.ValidationError({'expensetype': 'Expense type is not active.'})
        if expensetype.organisation_id != organisation.id:
            raise serializers.ValidationError({'expensetype': 'Expense type does not belong to the selected organisation.'})

        person = getattr(user, 'person', None)
        person_type = getattr(person, 'type', None)
        if person_type and expensetype.persontype not in (person_type, None):
            raise PermissionDenied('Expense type is not available for this user.')

        if accountdimension and accountdimension.organisation_id != organisation.id:
            raise serializers.ValidationError({'accountdimension': 'Cost centre does not belong to the selected organisation.'})

        if expensetype.requires_receipt and not receipt:
            raise serializers.ValidationError({'receipt': 'This expense type requires a receipt.'})
        if expensetype.requires_endtime and not ended_at:
            raise serializers.ValidationError({'ended_at': 'This expense type requires an ending date and time.'})

        upload = attrs.get('receipt')
        if upload and upload.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError({'receipt': 'Please choose a smaller file.'})

        return attrs
