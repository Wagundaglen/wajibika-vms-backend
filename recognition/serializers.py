# recognition/serializers.py
from rest_framework import serializers
from .models import Recognition

class RecognitionSerializer(serializers.ModelSerializer):
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)

    class Meta:
        model = Recognition
        fields = [
            'id', 'recipient', 'recipient_username', 'recognition_type',
            'title', 'description', 'points_awarded', 'date_awarded',
            'badge', 'certificate'
        ]
        read_only_fields = ['date_awarded', 'recipient_username']

    def validate(self, attrs):
        """
        Ensure only admins can set recipient explicitly.
        Volunteers shouldn't assign recognitions.
        """
        request = self.context.get('request')
        if request and not request.user.is_staff:
            if 'recipient' in attrs:
                raise serializers.ValidationError("You cannot assign recognitions.")
        return attrs
