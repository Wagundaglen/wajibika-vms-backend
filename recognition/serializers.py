from rest_framework import serializers
from .models import Recognition

class RecognitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recognition
        fields = '__all__'
        read_only_fields = ['date_awarded']
