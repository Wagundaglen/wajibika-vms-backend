from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'assigned_to',
            'assigned_to_name',
            'due_date',
            'status',
            'acceptance_status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'assigned_to_name']

class TaskAcceptanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['acceptance_status']
