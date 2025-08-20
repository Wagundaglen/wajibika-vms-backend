from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from feedback.models import FeedbackCategory, Feedback, FeedbackResponse
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample feedback data'

    def handle(self, *args, **options):
        # Create categories
        categories = [
            ('General', 'General feedback and suggestions'),
            ('Technical', 'Technical issues and system feedback'),
            ('Organizational', 'Organizational and procedural feedback'),
            ('Safety', 'Safety concerns and suggestions'),
            ('Training', 'Training and development feedback'),
        ]
        
        for name, desc in categories:
            FeedbackCategory.objects.get_or_create(name=name, defaults={'description': desc})
        
        # Get users
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.WARNING('No users found. Please create users first.'))
            return
        
        # Sample feedback data
        sample_feedback = [
            {
                'title': 'Great volunteer experience',
                'message': 'I really enjoyed volunteering with the team. Everyone was supportive and the work was meaningful. The coordination was excellent and I felt like I was making a real difference in the community.',
                'type': 'compliment',
                'sentiment': 'positive',
                'priority': 'low',
                'category_name': 'General'
            },
            {
                'title': 'Communication could be improved',
                'message': 'Sometimes it\'s hard to get updates about events and changes in schedule. Better communication channels would help volunteers stay informed and plan their time more effectively.',
                'type': 'suggestion',
                'sentiment': 'neutral',
                'priority': 'medium',
                'category_name': 'Organizational'
            },
            {
                'title': 'Safety equipment needs attention',
                'message': 'Some of the safety equipment at the construction site is outdated and needs replacement. This poses a risk to volunteers and should be addressed urgently.',
                'type': 'issue_report',
                'sentiment': 'negative',
                'priority': 'high',
                'category_name': 'Safety'
            },
            {
                'title': 'Training materials need updating',
                'message': 'The training materials haven\'t been updated in years and don\'t reflect current best practices. This affects the quality of volunteer work and safety standards.',
                'type': 'suggestion',
                'sentiment': 'negative',
                'priority': 'medium',
                'category_name': 'Training'
            },
            {
                'title': 'Excellent event coordination',
                'message': 'The community outreach event was very well organized. From setup to cleanup, everything ran smoothly. The team did an amazing job coordinating volunteers and resources.',
                'type': 'compliment',
                'sentiment': 'positive',
                'priority': 'low',
                'category_name': 'General'
            },
            {
                'title': 'Need more flexible scheduling',
                'message': 'As a volunteer with a full-time job, I need more flexible scheduling options. The current time slots don\'t accommodate volunteers who can only commit to weekends or evenings.',
                'type': 'suggestion',
                'sentiment': 'neutral',
                'priority': 'medium',
                'category_name': 'Organizational'
            },
            {
                'title': 'Website navigation issues',
                'message': 'The volunteer portal website has some navigation issues that make it difficult to find information quickly. The menu structure could be improved for better user experience.',
                'type': 'issue_report',
                'sentiment': 'negative',
                'priority': 'medium',
                'category_name': 'Technical'
            },
            {
                'title': 'Great mentorship program',
                'message': 'The mentorship program for new volunteers is excellent! Experienced volunteers take time to guide newcomers, which really helps with confidence and skill development.',
                'type': 'compliment',
                'sentiment': 'positive',
                'priority': 'low',
                'category_name': 'Training'
            }
        ]
        
        # Create feedback
        categories = list(FeedbackCategory.objects.all())
        for i, feedback_data in enumerate(sample_feedback):
            user = random.choice(users) if i % 3 != 0 else None  # Some anonymous feedback
            
            category = FeedbackCategory.objects.get(name=feedback_data['category_name'])
            
            Feedback.objects.create(
                user=user,
                is_anonymous=user is None,
                anonymous_name='Anonymous User' if user is None else None,
                category=category,
                feedback_type=feedback_data['type'],
                title=feedback_data['title'],
                message=feedback_data['message'],
                sentiment=feedback_data['sentiment'],
                priority=feedback_data['priority']
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {len(sample_feedback)} sample feedback entries'
            )
        )