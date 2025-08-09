from rest_framework import serializers
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    from_user_username = serializers.CharField(source='from_user.username', read_only=True)
    to_user_username = serializers.CharField(source='to_user.username', read_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id',
            'from_user', 'from_user_username',
            'to_user', 'to_user_username',
            'message', 'response',
            'anonymous', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['from_user', 'from_user_username', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user

        # If volunteer, force from_user to themselves unless anonymous
        if not user.is_staff:
            if not validated_data.get('anonymous', False):
                validated_data['from_user'] = user
            # Default to_user to None (Admin)
            validated_data['to_user'] = None

        return super().create(validated_data)
