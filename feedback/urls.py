from rest_framework.routers import DefaultRouter
from .views import FeedbackViewSet

router = DefaultRouter()
router.register(r'', FeedbackViewSet)  # Empty string for cleaner URL

urlpatterns = router.urls
