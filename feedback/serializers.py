from rest_framework import serializers
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['from_user', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        if not validated_data.get('anonymous', False):
            validated_data['from_user'] = user
        return super().create(validated_data)
