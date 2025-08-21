from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    # Home page
    path('', TemplateView.as_view(template_name="home.html"), name="home"),
    # Accounts app (register, login, profile)
    path('accounts/', include('accounts.urls')),
    # Other feature modules (using templates, not APIs)
    path('tasks/', include('tasks.urls')),
    
    # Redirect from old notifications path to communication
    path('notifications/', lambda request: redirect('communication:dashboard'), name='notifications_redirect'),
    
    # Communication app with namespace 'communication'
    path('communication/', include(('communication.urls', 'communication'), namespace='communication')),
    
    path('training/', include('training.urls')),
    path('feedback/', include('feedback.urls')),
    path('recognition/', include('recognition.urls')),
]

# Serve media and static in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)