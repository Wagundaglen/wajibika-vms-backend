# accounts/context_processors.py
from django.db.models import Count, Q, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def notifications(request):
    if not request.user.is_authenticated:
        return {'notifications': []}
    
    notifications = []
    user = request.user
    
    # Get unread tasks
    try:
        from tasks.models import Task
        unread_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['Pending', 'In Progress'],
            acceptance_status__in=['Pending', 'Accepted']
        ).order_by('-created_at')[:5]
        
        for task in unread_tasks:
            notifications.append({
                'type': 'task',
                'message': f'New task assigned: {task.title}',
                'timestamp': task.created_at,
                'link': f'/accounts/tasks/{task.id}/'
            })
    except ImportError:
        pass
    
    # Get unread messages and announcements
    try:
        from communication.models import Message, Announcement
        # Unread messages
        unread_messages = Message.objects.filter(
            recipient=user,
            is_read=False
        ).order_by('-timestamp')[:5]
        
        for message in unread_messages:
            notifications.append({
                'type': 'communication',
                'message': f'New message from {message.sender.username}',
                'timestamp': message.timestamp,
                'link': f'/accounts/communication/messages/{message.id}/'
            })
        
        # New announcements that target the user's role
        user_role = getattr(user, 'role', '')
        new_announcements = Announcement.objects.filter(
            is_active=True,
            target_roles__contains=user_role
        ).order_by('-created_at')[:5]
        
        for announcement in new_announcements:
            notifications.append({
                'type': 'communication',
                'message': f'New announcement: {announcement.title}',
                'timestamp': announcement.created_at,
                'link': f'/accounts/communication/announcements/{announcement.id}/'
            })
    except ImportError:
        pass
    
    # Get new training assignments
    try:
        from training.models import TrainingAssignment
        # Get training assignments for the current user that are not completed
        training_assignments = TrainingAssignment.objects.filter(
            volunteer=user,
            status__in=['assigned', 'in_progress']
        ).order_by('-assigned_date')[:5]
        
        for assignment in training_assignments:
            notifications.append({
                'type': 'training',
                'message': f'New training available: {assignment.course.title}',
                'timestamp': assignment.assigned_date,
                'link': f'/accounts/training/assignments/{assignment.id}/'
            })
    except ImportError:
        pass
    
    # Get feedback notifications
    try:
        from feedback.models import Feedback, FeedbackResponse
        
        # For Admins and Coordinators: unassigned or open feedback
        if user.role in ['Admin', 'Coordinator']:
            open_feedback = Feedback.objects.filter(
                Q(assigned_to=user) | Q(assigned_to__isnull=True),
                status__in=['open', 'in_progress']
            ).order_by('-created_at')[:5]
            
            for feedback in open_feedback:
                notifications.append({
                    'type': 'feedback',
                    'message': f'New feedback: {feedback.title}',
                    'timestamp': feedback.created_at,
                    'link': f'/accounts/feedback/{feedback.id}/'
                })
        
        # For any user: responses to their feedback
        user_feedback_responses = FeedbackResponse.objects.filter(
            feedback__user=user,
            created_at__gte=timezone.now() - timedelta(days=7)  # Last 7 days
        ).order_by('-created_at')[:5]
        
        for response in user_feedback_responses:
            notifications.append({
                'type': 'feedback',
                'message': f'Response to your feedback: {response.feedback.title}',
                'timestamp': response.created_at,
                'link': f'/accounts/feedback/{response.feedback.id}/'
            })
    except ImportError:
        pass
    
    # Get recognition notifications
    try:
        from recognition.models import Recognition, RecognitionProfile
        
        # Check if user has a volunteer profile
        try:
            volunteer_profile = RecognitionProfile.objects.get(volunteer=user)
        except RecognitionProfile.DoesNotExist:
            volunteer_profile = None
        
        # For any user: recognitions they received
        if volunteer_profile:
            recent_recognitions = Recognition.objects.filter(
                volunteer=user,
                created_at__gte=timezone.now() - timedelta(days=7)  # Last 7 days
            ).order_by('-created_at')[:5]
            
            for recognition in recent_recognitions:
                badge_name = recognition.badge.name if recognition.badge else "Recognition"
                notifications.append({
                    'type': 'recognition',
                    'message': f'You received {badge_name}: {recognition.message or "No message"}',
                    'timestamp': recognition.created_at,
                    'link': f'/accounts/recognition/{recognition.id}/'
                })
        
        # For Admins and Coordinators: new recognitions that might need review
        if user.role in ['Admin', 'Coordinator']:
            # Get recognitions from the last 3 days
            new_recognitions = Recognition.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=3)
            ).order_by('-created_at')[:5]
            
            for recognition in new_recognitions:
                notifications.append({
                    'type': 'recognition',
                    'message': f'New recognition given to {recognition.volunteer.username}',
                    'timestamp': recognition.created_at,
                    'link': f'/accounts/recognition/{recognition.id}/'
                })
    except ImportError:
        pass
    
    # Sort all notifications by timestamp
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to 10 most recent notifications
    notifications = notifications[:10]
    
    return {'notifications': notifications}