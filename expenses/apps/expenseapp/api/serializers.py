from rest_framework import serializers
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
    class Meta:
        model = ExpenseLine
        fields = [
            'id', 'description', 'begin_at', 'ended_at', 'expensetype',
            'accountdimension', 'basis', 'receipt', 'expense', 
            'user', 'organisation'
        ]
        read_only_fields = ['expense', 'user']
