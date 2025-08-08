from rest_framework import serializers
from .models import TrainingModule, TrainingProgress

class TrainingModuleSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TrainingModule
        fields = [
            'id', 'title', 'description', 'content_type', 'content',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'created_by_username']


class TrainingProgressSerializer(serializers.ModelSerializer):
    volunteer_username = serializers.CharField(source='volunteer.username', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True)

    class Meta:
        model = TrainingProgress
        fields = [
            'id', 'volunteer', 'volunteer_username', 'module', 'module_title',
            'status', 'completed_at', 'created_at'
        ]
        read_only_fields = [
            'volunteer_username', 'module_title', 'completed_at', 'created_at'
        ]
