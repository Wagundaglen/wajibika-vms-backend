from rest_framework.routers import DefaultRouter
from .views import RecognitionViewSet

router = DefaultRouter()
router.register(r'recognition', RecognitionViewSet)

urlpatterns = router.urls
