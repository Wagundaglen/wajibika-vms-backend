from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .serializers import RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        # Map user.role to existing group name in admin
        role_group_map = {
            "Volunteer": "Volunteers",
            "Coordinator": "Coordinators",
            "Admin": "Admins"
        }

        # Assign to group if mapping exists
        group_name = role_group_map.get(user.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)  # Use existing group
                user.groups.add(group)
            except Group.DoesNotExist:
                pass  # Skip if group not found

        # Give full admin rights if role is Admin
        if user.role == "Admin":
            user.is_staff = True
            user.is_superuser = True
            user.save()

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "phone": getattr(user, 'phone', None),
            "skills": getattr(user, 'skills', None),
            "role": getattr(user, 'role', None),
            "groups": list(user.groups.values_list('name', flat=True))
        })
