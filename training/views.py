# training/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg, ExpressionWrapper, F, DurationField
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
import uuid

from .models import (
    TrainingCourse, TrainingModule, TrainingAssignment, 
    TrainingProgress, Certificate
)
from accounts.models import Volunteer
from .forms import TrainingCourseForm, TrainingModuleForm, TrainingAssignmentForm

# Helper functions for role checking
def is_admin(user):
    return user.is_staff or user.role == 'Admin'

def is_coordinator(user):
    return user.role == 'Coordinator'

def is_volunteer(user):
    return user.role == 'Volunteer'

# Dashboard views
@login_required
def training_dashboard(request):
    """Main training dashboard that redirects to role-specific dashboard"""
    if is_admin(request.user):
        return redirect('training:admin_dashboard')
    elif is_coordinator(request.user):
        return redirect('training:coordinator_dashboard')
    elif is_volunteer(request.user):
        return redirect('training:volunteer_dashboard')
    else:
        messages.error(request, "You don't have permission to access the training system.")
        return redirect('home')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin training dashboard with overview statistics"""
    # Get training statistics
    total_courses = TrainingCourse.objects.count()
    total_modules = TrainingModule.objects.count()
    total_assignments = TrainingAssignment.objects.count()
    active_assignments = TrainingAssignment.objects.filter(status='in_progress').count()
    completed_assignments = TrainingAssignment.objects.filter(status='completed').count()
    
    # Calculate average completion time
    completed_assignments_with_time = TrainingAssignment.objects.filter(
        status='completed',
        progress__completed_at__isnull=False
    ).annotate(
        completion_time=ExpressionWrapper(
            F('progress__completed_at') - F('assigned_date'),
            output_field=DurationField()
        )
    )
    
    avg_completion_time = None
    if completed_assignments_with_time.exists():
        avg_completion_time = completed_assignments_with_time.aggregate(
            avg_time=Avg('completion_time')
        )['avg_time']
    
    # Get recent assignments
    recent_assignments = TrainingAssignment.objects.order_by('-assigned_date')[:10]
    
    # Get courses with most assignments
    popular_courses = TrainingCourse.objects.annotate(
        assignment_count=Count('trainingassignment')
    ).order_by('-assignment_count')[:5]
    
    context = {
        'total_courses': total_courses,
        'total_modules': total_modules,
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
        'avg_completion_time': avg_completion_time,
        'recent_assignments': recent_assignments,
        'popular_courses': popular_courses,
    }
    
    return render(request, 'training/admin_dashboard.html', context)

@login_required
@user_passes_test(is_coordinator)
def coordinator_dashboard(request):
    """Coordinator training dashboard with team-specific statistics"""
    # Try to get team volunteers if Team model exists
    try:
        from accounts.models import Team
        try:
            coordinator = request.user
            team_volunteers = Volunteer.objects.filter(team=coordinator.team)
        except:
            team_volunteers = []
    except ImportError:
        # If Team model doesn't exist, get all volunteers
        team_volunteers = Volunteer.objects.all()
    
    # Get team assignments
    team_assignments = TrainingAssignment.objects.filter(volunteer__in=team_volunteers)
    
    # Calculate statistics
    total_team_assignments = team_assignments.count()
    team_active_assignments = team_assignments.filter(status='in_progress').count()
    team_completed_assignments = team_assignments.filter(status='completed').count()
    
    completion_rate = 0
    if total_team_assignments > 0:
        completion_rate = int((team_completed_assignments / total_team_assignments) * 100)
    
    # Get volunteers with their progress
    volunteer_progress = []
    for volunteer in team_volunteers:
        vol_assignments = team_assignments.filter(volunteer=volunteer)
        total = vol_assignments.count()
        completed = vol_assignments.filter(status='completed').count()
        in_progress = vol_assignments.filter(status='in_progress').count()
        
        progress_percent = 0
        if total > 0:
            progress_percent = int((completed / total) * 100)
        
        volunteer_progress.append({
            'volunteer': volunteer,
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'progress_percent': progress_percent,
        })
    
    # Get recent team assignments
    recent_team_assignments = team_assignments.order_by('-assigned_date')[:10]
    
    context = {
        'team_volunteers': team_volunteers,
        'total_team_assignments': total_team_assignments,
        'team_active_assignments': team_active_assignments,
        'team_completed_assignments': team_completed_assignments,
        'completion_rate': completion_rate,
        'volunteer_progress': volunteer_progress,
        'recent_team_assignments': recent_team_assignments,
    }
    
    return render(request, 'training/coordinator_dashboard.html', context)

@login_required
@user_passes_test(is_volunteer)
def volunteer_dashboard(request):
    """Volunteer training dashboard with personal training status"""
    try:
        volunteer = request.user  # Since Volunteer extends AbstractUser, request.user is already a Volunteer
        assignments = TrainingAssignment.objects.filter(volunteer=volunteer)
    except:
        assignments = TrainingAssignment.objects.none()
    
    # Calculate statistics
    assigned_courses = assignments.count()
    in_progress = assignments.filter(status='in_progress').count()
    completed = assignments.filter(status='completed').count()
    
    # Get assignments grouped by status
    active_assignments = assignments.filter(status='in_progress')
    completed_assignments = assignments.filter(status='completed')
    upcoming_assignments = assignments.filter(status='assigned')
    
    context = {
        'assigned_courses': assigned_courses,
        'in_progress': in_progress,
        'completed': completed,
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
        'upcoming_assignments': upcoming_assignments,
        # Add training stats for the dashboard widget
        'training_stats': {
            'assigned_courses': assigned_courses,
            'in_progress': in_progress,
            'completed': completed,
        }
    }
    
    # Use the accounts template instead of training template
    return render(request, 'dashboards/volunteer_dashboard.html', context)

# Course management views
@login_required
@user_passes_test(is_admin)
def course_list(request):
    """List all training courses"""
    courses = TrainingCourse.objects.all()
    
    # Filter by search query
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'training/course_list.html', context)

@login_required
@user_passes_test(is_admin)
def course_create(request):
    """Create a new training course"""
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Training course "{course.title}" created successfully.')
            return redirect('training:course_detail', pk=course.pk)
    else:
        form = TrainingCourseForm()
    
    return render(request, 'training/course_form.html', {
        'form': form,
        'title': 'Create Training Course',
        'action': 'Create'
    })

@login_required
@user_passes_test(is_admin)
def course_detail(request, pk):
    """View details of a training course"""
    course = get_object_or_404(TrainingCourse, pk=pk)
    modules = course.modules.all().order_by('order')
    assignments = TrainingAssignment.objects.filter(course=course)
    
    # Calculate course statistics
    total_assignments = assignments.count()
    completed_assignments = assignments.filter(status='completed').count()
    in_progress_assignments = assignments.filter(status='in_progress').count()
    
    completion_rate = 0
    if total_assignments > 0:
        completion_rate = int((completed_assignments / total_assignments) * 100)
    
    context = {
        'course': course,
        'modules': modules,
        'assignments': assignments,
        'total_assignments': total_assignments,
        'completed_assignments': completed_assignments,
        'in_progress_assignments': in_progress_assignments,
        'completion_rate': completion_rate,
    }
    
    return render(request, 'training/course_detail.html', context)

@login_required
@user_passes_test(is_admin)
def course_update(request, pk):
    """Update a training course"""
    course = get_object_or_404(TrainingCourse, pk=pk)
    
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Training course "{course.title}" updated successfully.')
            return redirect('training:course_detail', pk=course.pk)
    else:
        form = TrainingCourseForm(instance=course)
    
    return render(request, 'training/course_form.html', {
        'form': form,
        'course': course,
        'title': 'Update Training Course',
        'action': 'Update'
    })

@login_required
@user_passes_test(is_admin)
def course_delete(request, pk):
    """Delete a training course"""
    course = get_object_or_404(TrainingCourse, pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, f'Training course "{course.title}" deleted successfully.')
        return redirect('training:course_list')
    
    return render(request, 'training/course_confirm_delete.html', {
        'course': course,
    })

# Module management views
@login_required
@user_passes_test(is_admin)
def module_create(request, course_pk):
    """Create a new module for a course"""
    course = get_object_or_404(TrainingCourse, pk=course_pk)
    
    if request.method == 'POST':
        form = TrainingModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, f'Training module "{module.title}" created successfully.')
            return redirect('training:course_detail', pk=course.pk)
    else:
        form = TrainingModuleForm()
    
    return render(request, 'training/module_form.html', {
        'form': form,
        'course': course,
        'title': 'Create Training Module',
        'action': 'Create'
    })

@login_required
@user_passes_test(is_admin)
def module_update(request, pk):
    """Update a training module"""
    module = get_object_or_404(TrainingModule, pk=pk)
    
    if request.method == 'POST':
        form = TrainingModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, f'Training module "{module.title}" updated successfully.')
            return redirect('training:course_detail', pk=module.course.pk)
    else:
        form = TrainingModuleForm(instance=module)
    
    return render(request, 'training/module_form.html', {
        'form': form,
        'module': module,
        'title': 'Update Training Module',
        'action': 'Update'
    })

@login_required
@user_passes_test(is_admin)
def module_delete(request, pk):
    """Delete a training module"""
    module = get_object_or_404(TrainingModule, pk=pk)
    course_pk = module.course.pk
    
    if request.method == 'POST':
        module.delete()
        messages.success(request, f'Training module "{module.title}" deleted successfully.')
        return redirect('training:course_detail', pk=course_pk)
    
    return render(request, 'training/module_confirm_delete.html', {
        'module': module,
    })

# Assignment management views
@login_required
def assignment_list(request):
    """List training assignments based on user role"""
    if is_admin(request.user):
        assignments = TrainingAssignment.objects.all()
    elif is_coordinator(request.user):
        # Try to get team volunteers if Team model exists
        try:
            from accounts.models import Team
            try:
                coordinator = request.user
                team_volunteers = Volunteer.objects.filter(team=coordinator.team)
            except:
                team_volunteers = []
        except ImportError:
            # If Team model doesn't exist, get all volunteers
            team_volunteers = Volunteer.objects.all()
        
        assignments = TrainingAssignment.objects.filter(volunteer__in=team_volunteers)
    elif is_volunteer(request.user):
        try:
            volunteer = request.user  # Since Volunteer extends AbstractUser, request.user is already a Volunteer
            assignments = TrainingAssignment.objects.filter(volunteer=volunteer)
        except:
            assignments = TrainingAssignment.objects.none()
    else:
        assignments = TrainingAssignment.objects.none()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        assignments = assignments.filter(status=status_filter)
    
    # Filter by search query
    search_query = request.GET.get('search', '')
    if search_query:
        assignments = assignments.filter(
            Q(course__title__icontains=search_query) | 
            Q(volunteer__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'training/assignment_list.html', context)

@login_required
@user_passes_test(lambda u: is_admin(u) or is_coordinator(u))
def assign_training(request):
    """Assign training to volunteers"""
    try:
        if request.method == 'POST':
            form = TrainingAssignmentForm(request.POST)
            if form.is_valid():
                try:
                    assignment = form.save(commit=False)
                    assignment.assigned_by = request.user
                    assignment.assigned_date = timezone.now()
                    assignment.status = 'assigned'
                    assignment.save()
                    
                    # Create training progress for each module in the course
                    modules = assignment.course.modules.all()
                    for module in modules:
                        TrainingProgress.objects.get_or_create(
                            assignment=assignment,
                            module=module
                        )
                    
                    # Send notification to volunteer
                    from communication.models import Notification
                    Notification.objects.create(
                        recipient=assignment.volunteer,
                        message=f"📚 New training assigned: {assignment.course.title}",
                        category="training",
                        link=f"/training/assignments/{assignment.pk}/"
                    )
                    
                    # Send email notification
                    send_training_assignment_notification(assignment)
                    
                    messages.success(request, 
                        f'Training "{assignment.course.title}" assigned to {assignment.volunteer.username} successfully.')
                    return redirect('training:assignment_detail', pk=assignment.pk)
                except Exception as e:
                    messages.error(request, f'Error saving assignment: {str(e)}')
            else:
                # Form is invalid, show errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = TrainingAssignmentForm()
            
            # Pre-select volunteer if provided in URL
            volunteer_id = request.GET.get('volunteer')
            if volunteer_id:
                try:
                    volunteer = Volunteer.objects.get(pk=volunteer_id)
                    form.fields['volunteer'].initial = volunteer
                except Volunteer.DoesNotExist:
                    messages.warning(request, "Selected volunteer not found.")
        
        return render(request, 'training/assignment_form.html', {
            'form': form,
            'title': 'Assign Training',
            'action': 'Assign'
        })
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('training:assignment_list')

@login_required
def assignment_detail(request, pk):
    """View details of a training assignment"""
    # Use select_related to fetch related objects in a single query
    assignment = get_object_or_404(
        TrainingAssignment.objects.select_related('assigned_by', 'volunteer', 'course'),
        pk=pk
    )
    
    # Check permissions
    if not is_admin(request.user) and assignment.volunteer != request.user:
        try:
            coordinator = request.user
            if hasattr(assignment.volunteer, 'team') and assignment.volunteer.team != coordinator.team:
                return redirect('training:training_dashboard')
        except:
            return redirect('training:training_dashboard')
    
    # Use prefetch_related for better performance with related progress items
    progress_items = TrainingProgress.objects.filter(
        assignment=assignment
    ).select_related('module').order_by('module__order')
    
    # Calculate progress
    total_modules = progress_items.count()
    completed_modules = progress_items.filter(is_completed=True).count()
    progress_percent = 0
    if total_modules > 0:
        progress_percent = int((completed_modules / total_modules) * 100)
    
    # Prepare assigned_by_display for the template
    if assignment.assigned_by:
        assigned_by_display = assignment.assigned_by.get_full_name() or assignment.assigned_by.username
    else:
        assigned_by_display = "System"  # Or "Not specified" if you prefer
    
    context = {
        'assignment': assignment,
        'progress_items': progress_items,
        'total_modules': total_modules,
        'completed_modules': completed_modules,
        'progress_percent': progress_percent,
        'assigned_by_display': assigned_by_display,  # Add this to context
    }
    
    return render(request, 'training/assignment_detail.html', context)

@login_required
@user_passes_test(lambda u: is_admin(u) or is_coordinator(u))
def assignment_update(request, pk):
    """Update a training assignment"""
    assignment = get_object_or_404(TrainingAssignment, pk=pk)
    
    if request.method == 'POST':
        form = TrainingAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Training assignment updated successfully.')
            return redirect('training:assignment_detail', pk=assignment.pk)
    else:
        form = TrainingAssignmentForm(instance=assignment)
    
    return render(request, 'training/assignment_form.html', {
        'form': form,
        'assignment': assignment,
        'title': 'Update Training Assignment',
        'action': 'Update'
    })

@login_required
@user_passes_test(lambda u: is_admin(u) or is_coordinator(u))
def assignment_delete(request, pk):
    """Delete a training assignment"""
    assignment = get_object_or_404(TrainingAssignment, pk=pk)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Training assignment deleted successfully.')
        return redirect('training:assignment_list')
    
    return render(request, 'training/assignment_confirm_delete.html', {
        'assignment': assignment,
    })

# Training progress views
@login_required
def start_module(request, assignment_pk, module_pk):
    """Start a training module"""
    assignment = get_object_or_404(TrainingAssignment, pk=assignment_pk)
    module = get_object_or_404(TrainingModule, pk=module_pk)
    
    # Check permissions
    if assignment.volunteer != request.user:
        return redirect('training:training_dashboard')
    
    progress, created = TrainingProgress.objects.get_or_create(
        assignment=assignment,
        module=module,
        defaults={'started_at': timezone.now()}
    )
    
    if not progress.started_at:
        progress.started_at = timezone.now()
        progress.save()
    
    # Update assignment status if it was just assigned
    if assignment.status == 'assigned':
        assignment.status = 'in_progress'
        assignment.save()
    
    return render(request, 'training/module_view.html', {
        'assignment': assignment,
        'module': module,
        'progress': progress,
    })

@login_required
def complete_module(request, assignment_pk, module_pk):
    """Mark a module as completed"""
    assignment = get_object_or_404(TrainingAssignment, pk=assignment_pk)
    module = get_object_or_404(TrainingModule, pk=module_pk)
    
    # Check permissions
    if assignment.volunteer != request.user:
        return redirect('training:training_dashboard')
    
    try:
        progress = TrainingProgress.objects.get(assignment=assignment, module=module)
        progress.mark_completed()
        messages.success(request, f'Module "{module.title}" completed successfully!')
    except TrainingProgress.DoesNotExist:
        messages.error(request, 'Module progress not found.')
    
    return redirect('training:assignment_detail', pk=assignment_pk)

# Certificate views
@login_required
def view_certificate(request, pk):
    """View a training certificate"""
    certificate = get_object_or_404(Certificate, pk=pk)
    
    # Check permissions
    if not is_admin(request.user) and certificate.assignment.volunteer != request.user:
        return redirect('training:training_dashboard')
    
    return render(request, 'training/certificate_view.html', {
        'certificate': certificate,
    })

@login_required
def download_certificate(request, pk):
    """Download a training certificate (placeholder for now)"""
    certificate = get_object_or_404(Certificate, pk=pk)
    
    # Check permissions
    if not is_admin(request.user) and certificate.assignment.volunteer != request.user:
        return redirect('training:training_dashboard')
    
    # For now, just show a message that PDF generation is not available
    messages.info(request, 'PDF certificate generation is not available at this time.')
    return redirect('training:view_certificate', pk=pk)

# Additional views for integrated functionality
@login_required
def my_training(request):
    """View personal training assignments (volunteer)"""
    try:
        # Since Volunteer extends AbstractUser, request.user is already a Volunteer
        volunteer = request.user
        assignments = TrainingAssignment.objects.filter(volunteer=volunteer)
        
        # Group assignments by status
        active_assignments = assignments.filter(status='in_progress')
        completed_assignments = assignments.filter(status='completed')
        upcoming_assignments = assignments.filter(status='assigned')
        failed_assignments = assignments.filter(status='failed')
        
        context = {
            'assignments': assignments,
            'active_assignments': active_assignments,
            'completed_assignments': completed_assignments,
            'upcoming_assignments': upcoming_assignments,
            'failed_assignments': failed_assignments,
        }
        
        return render(request, 'training/my_training.html', context)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in my_training view: {e}")
        # Return a simple error message
        return render(request, 'training/my_training.html', {'error': str(e)})

@login_required
def my_certificates(request):
    """View personal certificates (volunteer)"""
    try:
        # Since Volunteer extends AbstractUser, request.user is already a Volunteer
        volunteer = request.user
        certificates = Certificate.objects.filter(assignment__volunteer=volunteer)
        
        context = {
            'certificates': certificates,
        }
        
        return render(request, 'training/my_certificates.html', context)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in my_certificates view: {e}")
        # Return a simple error message
        return render(request, 'training/my_certificates.html', {'error': str(e)})

@login_required
@user_passes_test(is_coordinator)
def team_progress(request):
    """View team training progress (coordinator)"""
    # Try to get team volunteers if Team model exists
    try:
        from accounts.models import Team
        try:
            coordinator = request.user
            team_volunteers = Volunteer.objects.filter(team=coordinator.team)
        except:
            team_volunteers = []
    except ImportError:
        # If Team model doesn't exist, get all volunteers
        team_volunteers = Volunteer.objects.all()
    
    # Get team assignments
    team_assignments = TrainingAssignment.objects.filter(volunteer__in=team_volunteers)
    
    # Get volunteers with their progress
    volunteer_progress = []
    for volunteer in team_volunteers:
        vol_assignments = team_assignments.filter(volunteer=volunteer)
        total = vol_assignments.count()
        completed = vol_assignments.filter(status='completed').count()
        in_progress = vol_assignments.filter(status='in_progress').count()
        
        progress_percent = 0
        if total > 0:
            progress_percent = int((completed / total) * 100)
        
        volunteer_progress.append({
            'volunteer': volunteer,
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'progress_percent': progress_percent,
        })
    
    context = {
        'volunteer_progress': volunteer_progress,
    }
    
    return render(request, 'training/team_progress.html', context)

# Helper functions
def send_training_assignment_notification(assignment):
    """Send email notification for training assignment"""
    subject = f"New Training Assignment: {assignment.course.title}"
    message = f"""
    Dear {assignment.volunteer.get_full_name() or assignment.volunteer.username},
    
    You have been assigned a new training course: {assignment.course.title}
    
    {assignment.course.description}
    
    Please log in to your account to start the training.
    
    Due date: {assignment.due_date.strftime('%B %d, %Y') if assignment.due_date else 'No due date'}
    
    Thank you,
    Wajibika Initiative Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [assignment.volunteer.email],
        fail_silently=True,
    )