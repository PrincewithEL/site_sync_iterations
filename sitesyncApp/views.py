from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Bookmarks, Users, OTP, Profile, Projects, User, ProjectMembers, Chat, GroupChat, ChatStatus, Resources, Events, Tasks, Transactions
from django.core.mail import send_mail
import re
import hashlib
from django.contrib.auth.hashers import make_password, check_password
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import uuid
from datetime import timedelta
from django.contrib.auth.models import User
import logging
from datetime import date
from django.utils.encoding import smart_str
from datetime import datetime
import random
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import pytz
from social_django.utils import load_strategy
from django.http import JsonResponse
from .chatbot import get_response 
import json
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q

logger = logging.getLogger(__name__)

# Create your views here.

def home(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        user_id = request.session.get('user_id')
        
        if user_id:
            try:
                # Get the OTP entry for the user
                otp = OTP.objects.get(user_id=user_id, otp_code=otp_code, used=False)

                # Check if OTP is within the last 15 minutes
                if otp.created_at >= timezone.now() - timedelta(minutes=15):
                    otp.used = True  # Mark the OTP as used
                    otp.save()

                    # Redirect based on user type
                    if hasattr(request.user, 'profile'):
                        if request.user.profile.user_type == 'Admin':
                            return render(request, 'admin1.html')  # Ensure 'admin' matches your URL name
                        elif request.user.profile.user_type == 'Client':
                            return render(request, 'dashboard.html')  # Ensure 'client' matches your URL name
                        elif request.user.profile.user_type == 'Contractor':
                            return render(request, 'dashboard.html')  # Ensure 'contractor' matches your URL name
                    else:
                        # Handle cases where profile doesn't exist
                        return redirect('home')  # Ensure 'home' matches your URL name

                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return render(request, 'otp.html')

            except OTP.DoesNotExist:
                messages.error(request, 'Invalid OTP.')
                return render(request, 'otp.html')

    # If it's not a POST request or OTP verification failed, render index.html
    return render(request, 'index.html')

def home1(request):
    return render(request, 'home.html')

@login_required
def admin1(request):
    return render(request, 'admin1.html')

def get_chatbot_response(request):
    if request.method == 'POST':
        prompt = json.loads(request.body).get('prompt', '')
        response = get_response(prompt)
        return JsonResponse({'response': response})

@login_required
def resources(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    type = profile.user_type
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    resources = Resources.objects.filter(project_id=pk, is_deleted=0)
    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Resource', project_id=project.project_id, user_id=request.user.id)
    bookmarked_resources_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_resources = Resources.objects.filter(resource_id__in=bookmarked_resources_ids)
    all_resources = (resources | bookmarked_resources).distinct()
    bookmark_resources_count = bookmarked_resources.count()
    trash_resources = Resources.objects.filter(project_id=pk, is_deleted=1)    
    resource_count = all_resources.count()
    video_count = all_resources.filter(resource_type='Video').count()
    document_count = all_resources.filter(resource_type='Document').count()
    audio_count = all_resources.filter(resource_type='Audio').count()
    image_count = all_resources.filter(resource_type='Image').count()    
    trash_resources_count = trash_resources.count()

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    unread_chat_counts = {}
    pending_tasks_counts = {}

    all_unread_chats = []
    all_pending_tasks = []

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id)
            all_unread_chats = ChatStatus.objects.filter(
                user_id=profile.user_id,
                group_id=group_chat.group_id,
                status=1,
                is_deleted=0
            )
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )
            unread_chat_counts[project1.project_id] = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_chat_counts[project1.project_id] = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0
        ).exclude(
            task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
        )
        pending_tasks_counts[project1.project_id] = all_pending_tasks.count()

    date_filter_display = "All Time"
    status_filter_display = "All Resources"

    if request.method == "POST":
        action = request.POST.get('action')
        action1 = request.POST.get('action1')
        selected_resource_ids = request.POST.getlist('selected_resources')  # Handles multiple selections
        selected_resource_id = request.POST.get('selected_resource')  # Handles single selection
        
        # Debugging: Print received values
        print(f'action: {action}')
        print(f'action1: {action1}')
        print(f'selected_resource_ids: {selected_resource_ids}')
        print(f'selected_resource_id: {selected_resource_id}')
        
        # Handle actions based on POST data
        if action == 'bookmark':
            if selected_resource_ids:
                for resource_id in selected_resource_ids:
                    try:
                        item_id = int(resource_id)
                        bookmarkR = Bookmarks(
                            item_type='Resource',
                            item_id=item_id,
                            user_id=request.user.id,
                            project_id=project.project_id,
                            timestamp=timezone.now(),
                            is_deleted=0
                        )
                        bookmarkR.save()
                        messages.success(request, 'Resources bookmarked successfully.')
                    except ValueError:
                        messages.error(request, f'Invalid resource ID: {resource_id}.')
                        return HttpResponseBadRequest(f'Invalid resource ID: {resource_id}')
            else:
                messages.error(request, 'No resources selected for bookmarking.')
                return HttpResponseBadRequest('No resources selected')
        
        elif action == 'unbookmark':
            if selected_resource_ids:
                Bookmarks.objects.filter(
                    item_id__in=selected_resource_ids,
                    item_type='Resource',
                    user_id=request.user.id
                ).update(is_deleted=1)
                messages.success(request, 'Resources unbookmarked successfully.')
            else:
                messages.error(request, 'No resources selected for unbookmarking.')
                return HttpResponseBadRequest('No resources selected')

        elif action1 == 'bookmark1':
            if selected_resource_id:
                try:
                    item_id = int(selected_resource_id)
                    bookmarkR = Bookmarks(
                        item_type='Resource',
                        item_id=item_id,
                        user_id=request.user.id,
                        project_id=project.project_id,
                        timestamp=timezone.now(),
                        is_deleted=0
                    )
                    bookmarkR.save()
                    messages.success(request, 'Resource bookmarked successfully.')
                except ValueError:
                    messages.error(request, 'Invalid resource ID.')
                    return HttpResponseBadRequest('Invalid resource ID')
            else:
                messages.error(request, 'No resource selected for bookmarking.')
                return HttpResponseBadRequest('No resource selected')

        elif action1 == 'unbookmark1':
            if selected_resource_id:
                try:
                    item_id = int(selected_resource_id)
                    Bookmarks.objects.filter(
                        item_id=item_id,
                        item_type='Resource',
                        user_id=request.user.id
                    ).update(is_deleted=1)
                    messages.success(request, 'Resource unbookmarked successfully.')
                except ValueError:
                    messages.error(request, 'Invalid resource ID.')
                    return HttpResponseBadRequest('Invalid resource ID')
            else:
                messages.error(request, 'No resource selected for unbookmarking.')
                return HttpResponseBadRequest('No resource selected')

        elif action == 'delete1':
            if selected_resource_ids:
                Resources.objects.filter(resource_id__in=selected_resource_ids).update(is_deleted=2)
                messages.success(request, 'Resources permanently deleted.')
            else:
                messages.error(request, 'No resources selected for deletion.')
                return HttpResponseBadRequest('No resources selected')
        
        elif action == 'restore':
            if selected_resource_ids:
                Resources.objects.filter(resource_id__in=selected_resource_ids).update(is_deleted=0)
                messages.success(request, 'Resources restored successfully.')
            else:
                messages.error(request, 'No resources selected for restoration.')
                return HttpResponseBadRequest('No resources selected')

        action = None
        action1 = None
        selected_resource_ids = []
        selected_resource_id = []

        return redirect('resources', pk=pk)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        all_resources = all_resources.filter(Q(resource_name__icontains=search_query)|Q(resource_details__icontains=search_query))

    # Apply date filtering
    date_filter = request.GET.get('date_filter')
    if date_filter:
        if date_filter == 'today':
            all_projects = all_projects.filter(created_at__date=current_date)
            date_filter_display = "Today"
        elif date_filter == 'this_week':
            start_of_week = current_date - timedelta(days=current_date.weekday())
            all_projects = all_projects.filter(created_at__date__gte=start_of_week)
            date_filter_display = "This Week"
        elif date_filter == 'this_month':
            all_projects = all_projects.filter(created_at__year=current_date.year, created_at__month=current_date.month)
            date_filter_display = "This Month"
        elif date_filter == 'this_year':
            all_projects = all_projects.filter(created_at__year=current_date.year)
            date_filter_display = "This Year"

    # Get the filter type from the query parameters (default to 'all')
    filter_type = request.GET.get('filter', 'all')

    # Apply filtering based on the selected filter type
    if filter_type == 'Video':
        resources = all_resources.filter(resource_type='Video')
    elif filter_type == 'Image':
        resources = all_resources.filter(resource_type='Image')
    elif filter_type == 'Audio':
        resources = all_resources.filter(resource_type='Audio')
    elif filter_type == 'Document':
        resources = all_resources.filter(resource_type='Document')
    elif filter_type == 'video':
        resources = all_resources.filter(resource_type='Video')
    elif filter_type == 'image':
        resources = all_resources.filter(resource_type='Image')
    elif filter_type == 'audio':
        resources = all_resources.filter(resource_type='Audio')
    elif filter_type == 'document':
        resources = all_resources.filter(resource_type='Document')
    elif filter_type == 'bookmarked':
        resources = bookmarked_resources
    else:
        resources = all_resources

    # Implement pagination (3 resources per page)
    paginator = Paginator(resources, 3)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        resources = paginator.page(page_number)
    except (ValueError, EmptyPage):
        resources = paginator.page(1)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'resources': resources,
        'all_resources': all_resources,
        'trash_resources': trash_resources,
        'video_count': video_count,
        'document_count': document_count,
        'image_count': image_count,
        'audio_count': audio_count,
        'trash_resources_count': trash_resources_count,
        'bookmark_resources_count': bookmark_resources_count,
        'bookmarked_resources_ids': bookmarked_resources_ids,
        'leader_profile': leader_profile,
        'resource_count': resource_count,
        'status_filter_display': status_filter_display,
        'date_filter_display': date_filter_display,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'type': type,
    }
    return render(request, 'resources.html', context)

@login_required
def add_resource(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        file = request.FILES.get('resource_file')
        chat_file = None
        file_size = None

        if file:
            profile_picture = file
            unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
            profile_picture_path = default_storage.save(unique_filename, profile_picture)

            # Move the file to the desired directory under MEDIA_ROOT
            dest_path = os.path.join(settings.MEDIA_ROOT, 'project_resources', unique_filename)

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                chat_file = 'project_resources/' + unique_filename
                
                # Get file size in kilobytes (KB) or megabytes (MB)
                file_size = file.size
                if file_size < 1024:
                    file_size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    file_size_str = f"{file_size / 1024:.2f} KB"
                else:
                    file_size_str = f"{file_size / (1024 * 1024):.2f} MB"

            except Exception as e:
                messages.error(request, f"Error saving project file: {str(e)}")
                return redirect('resources', pk=pk)

        resource = Resources(
            user=request.user,
            project=project,
            resource_name=request.POST['resource_name'],
            resource_details=request.POST['resource_details'],
            resource_type=request.POST['resource_type'],
            resource_directory=chat_file,
            resource_size=file_size_str,
            is_deleted=0,
            resource_status='Active',
            created_at=timezone.now()
        )
        resource.save()
        
        return redirect('resources', pk=pk)
    return redirect('resources', pk=pk)

@login_required
def delete_resource(request, pk, resource_id):
    resource = get_object_or_404(Resources, pk=resource_id, project__pk=pk)
    resource.is_deleted = 1
    resource.save()
    return redirect('resources', pk=pk)

@login_required
def restore_resource(request, pk, resource_id):
    resource = get_object_or_404(Resources, pk=resource_id, project__pk=pk)
    resource.is_deleted = 0
    resource.save()
    return redirect('resources', pk=pk)

@login_required
def hide_resource(request, pk, resource_id):
    resource = get_object_or_404(Resources, pk=resource_id, project__pk=pk)
    resource.is_deleted = 2
    resource.save()
    return redirect('resources', pk=pk)

@login_required
def add_transaction(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        tp = float(request.POST['transaction_price']) * int(request.POST['transaction_quantity'])
        transaction = Transactions(
            user=request.user,
            project=project,
            transaction_name=request.POST['transaction_name'],
            transaction_details=request.POST['transaction_details'],
            transaction_price=float(request.POST['transaction_price']),
            transaction_quantity=int(request.POST['transaction_quantity']),
            transaction_votes_for=0,
            transaction_votes_against=0,
            total_transaction_price=float(request.POST['transaction_price']) * int(request.POST['transaction_quantity']),
            created_at=timezone.now(),
            transaction_status='Completed',
            is_deleted=0
        )
        transaction.save()

    newprice = project.estimated_budget - tp
    if tp > 0:
        project.actual_expenditure = tp
        project.balance = project.estimated_budget - project.actual_expenditure 
        project.save()
    else:
        messages.error(request, 'Price of Transaction exceeds the project budget, kindly try again.')
        return redirect('transactions', pk=pk)

        messages.success(request, '')
        return redirect('transactions', pk=pk)
    
    return redirect('transactions', pk=pk)

@login_required
def delete_transaction(request, pk, transaction_id):
    project = get_object_or_404(Projects, pk=pk)
    transactions = get_object_or_404(Transactions, pk=transaction_id, project__pk=pk)
    project.estimated_budget += transactions.total_transaction_price
    project.actual_expenditure -= transactions.total_transaction_price 
    project.balance = project.estimated_budget - project.actual_expenditure 
    project.save()
    transactions.is_deleted = 1
    transactions.save()
    return redirect('transactions', pk=pk)

@login_required
def transactions(request, pk):

    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # All tasks for the user in this project
    transactions = Transactions.objects.filter(project_id=pk, is_deleted=0)
    transaction_count = transactions.count()

  # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)

    # Retrieve user details for project members
    project_member_details = []
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)

    # user_votes = TransactionVote.objects.filter(user=request.user, transaction__project=project)
    # user_votes_dict = {vote.transaction_id: vote.vote for vote in user_votes}

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'transactions': transactions,
        'leader_profile': leader_profile,
        'project_members': project_member_details,
        'transaction_count': transaction_count,
        # 'user_votes': user_votes_dict,
    }
    return render(request, 'transactions.html', context)

@login_required
def edit_message(request, pk):
    if request.method == 'POST':
        message_id = request.POST.get('mid')
        new_message = request.POST.get('edited_message')
        chat = get_object_or_404(Chat, chat_id=message_id, sender_user=request.user)
        chat.message = new_message
        chat.timestamp = timezone.now()
        chat.save()
        return redirect('chat', pk=pk)
    return redirect('chat', pk=pk)

@login_required
def tasks_events(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # All tasks for the user in this project
    tasks = Tasks.objects.filter(project_id=pk, member_id=user.id, is_deleted=0)
    print(f"Total tasks for user {user.id}: {tasks.count()}")

    # Pending tasks (not completed)
    ptasks = Tasks.objects.filter(
        project_id=pk,
        member_id=profile.user_id,
        is_deleted=0
    ).exclude(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )
    print(f"Pending tasks for user {user.id}: {ptasks.count()}")

    # Completed tasks
    ctasks = Tasks.objects.filter(
        project_id=pk,
        member_id=profile.user_id,
        is_deleted=0
    ).filter(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )
    print(f"Completed tasks for user {user.id}: {ctasks.count()}")

    # Pending tasks (not completed)
    p1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0
    ).exclude(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )
    print(f"Total pending tasks for project {pk}: {p1tasks.count()}")

    # Completed tasks
    c1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0
    ).filter(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )
    print(f"Total completed tasks for project {pk}: {c1tasks.count()}")

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)

    # Retrieve user details for project members
    project_member_details = []
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)

    project_tasks = Tasks.objects.filter(project=project, is_deleted=0)

    events = Events.objects.filter(project_id=pk, user=user.id, is_deleted=0)
    pending_tasks = ptasks.count()
    completed_tasks = ctasks.count()
    pending_tasks1 = p1tasks.count()
    completed_tasks1 = c1tasks.count()

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'tasks': ptasks,
        'ctasks': ctasks,
        'p1tasks': p1tasks,
        'c1tasks': c1tasks,
        'events': events,
        'project_tasks': project_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks1': pending_tasks1,
        'completed_tasks1': completed_tasks1,
        'leader_profile': leader_profile,
        'pending_tasks': pending_tasks,
        'project_members': project_member_details,
    }
    return render(request, 'tasks_events.html', context)

@login_required
def add_event(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        
        # Parse date and time
        event_date = datetime.strptime(request.POST['event_date'], '%Y-%m-%d').date()
        event_start_time = datetime.strptime(request.POST['event_start_time'], '%H:%M').time()
        event_end_time = datetime.strptime(request.POST['event_end_time'], '%H:%M').time()

        event = Events(
            user=request.user,
            project=project,
            event_name=request.POST['event_name'],
            event_details=request.POST['event_details'],
            event_date=event_date,
            event_start_time=event_start_time,
            event_end_time=event_end_time,
            event_location=request.POST.get('event_location', ''),
            event_link=request.POST.get('event_link', ''),
            event_status='Scheduled',  # Initial status
            created_at=timezone.now(),
            is_deleted=0
        )

        event.save()
        
        messages.success(request, 'Event added successfully.')
        return redirect('tasks_events', pk=pk)  # Assuming you have a 'project_events' view
    
    # If not POST, redirect to the project events page
    return redirect('tasks_events', pk=pk)

@login_required
def delete_event(request, pk, event_id):
    event = get_object_or_404(Events, pk=event_id, project__pk=pk)
    event.is_deleted = 1
    event.save()
    return redirect('tasks_events', pk=pk)

@login_required
def add_task(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        
        # Get the member (assigned user) from the form
        member_id = request.POST.get('member')
        member = get_object_or_404(User, pk=member_id)

        # Parse dates
        task_given_date = timezone.now().date()
        task_due_date = datetime.strptime(request.POST['due_date'], '%Y-%m-%d').date()

        # Calculate days left
        days_left = (task_due_date - task_given_date).days

        task = Tasks(
            leader=request.user,  # Assuming the current user is the leader
            member=member,
            project=project,
            task_name=request.POST['task_name'],
            task_details=request.POST['task_details'],
            task_given_date=task_given_date,
            task_due_date=task_due_date,
            task_days_left=days_left,
            task_days_overdue=0,  # Initially 0
            task_percentage_complete=0,  # Initially 0%
            task_status='Ongoing',  # Initial status
            created_at=timezone.now(),
            is_deleted=0
        )

        # Handle dependent task if provided
        dependent_task_id = request.POST.get('dependent_task')
        if dependent_task_id:
            task.dependant_task_id = dependent_task_id

        task.save()
        
        messages.success(request, 'Task added successfully.')
        return redirect('tasks_events', pk=pk)  # Assuming you have a 'project_tasks' view
    
    # If not POST, redirect to the project tasks page
    return redirect('tasks_events', pk=pk)

@login_required
def delete_task(request, pk, task_id):
    task = get_object_or_404(Tasks, pk=task_id, project__pk=pk)
    task.is_deleted = 1
    task.save()
    return redirect('tasks_events', pk=pk)

@login_required
def complete_task(request, pk, task_id):
    task = get_object_or_404(Tasks, pk=task_id, project__pk=pk)
    task.task_status = 'Completed Today'
    task.task_completed_date = timezone.now().date()
    task.save()
    return redirect('tasks_events', pk=pk)

@login_required
def delete_project(request, pk):
    project = get_object_or_404(Projects, project_id=pk)

    # Check if the logged-in user is the project leader
    if project.project_leader != request.user:
        messages.error(request, "You do not have permission to delete this project.")
        return redirect('client')

    # Proceed with deletion if the user is the project leader
    project.is_deleted = 1
    project.save()
    messages.success(request, "Project deleted successfully.")
    return redirect('client')

@login_required
def restore_project(request, pk):
    project = get_object_or_404(Projects, project_id=pk)
    project.is_deleted = 0
    project.save()
    return redirect('client')

@login_required
def hide_project(request, pk):
    project = get_object_or_404(Projects, project_id=pk)
    project.is_deleted = 2
    project.save()
    return redirect('client')

@login_required
def chat(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)

    # Retrieve user details for project members
    project_member_details = []
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)

    # Fetch chat messages for the current project
    chat_messages = Chat.objects.filter(group=project.groupchat, is_deleted=0).order_by('timestamp')

    # Update chat status from 1 to 0 for the logged-in user
    ChatStatus.objects.filter(user_id=user.id, group=project.groupchat, status=1).update(status=0)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image1': profile.profile_picture.url if profile.profile_picture else None,
        'type': profile.user_type,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'leader_profile': leader_profile,
        'member_status': member.status,
        'project_member_details': project_member_details,
        'chat_messages': chat_messages,  
    }
    return render(request, 'chat.html', context)

@login_required
def project_detail(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    type = profile.user_type
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    leader_user = Users.objects.get(user_id=project.leader_id)

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    unread_chat_counts = {}
    pending_tasks_counts = {}

    all_unread_chats = []
    all_pending_tasks = []

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id)
            all_unread_chats = ChatStatus.objects.filter(
                user_id=profile.user_id,
                group_id=group_chat.group_id,
                status=1,
                is_deleted=0
            )
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )
            unread_chat_counts[project1.project_id] = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_chat_counts[project1.project_id] = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0
        ).exclude(
            task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
        )
        pending_tasks_counts[project1.project_id] = all_pending_tasks.count()

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)
    project_member_ids = project_members.values_list('user_id', flat=True)

    project_membersC = project_members.count()

    tasks = Tasks.objects.filter(project_id=pk, member_id=user.id, is_deleted=0)

    # Pending tasks (not completed)
    ptasks = Tasks.objects.filter(
        project_id=pk,
        member_id=user.id,
        is_deleted=0
    ).exclude(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )

    # Completed tasks
    ctasks = Tasks.objects.filter(
        project_id=pk,
        member_id=user.id,
        is_deleted=0
    ).filter(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )

    # Pending tasks (not completed)
    p1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0
    ).exclude(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )

    # Completed tasks
    c1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0
    ).filter(
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    )

    # Calculate the progress percentage for the project
    if project.end_date and project.start_date:
        total_project_days = (project.end_date - project.start_date).days
        days_passed = (now - project.start_date).days
        if total_project_days > 0:
            progress_percentage = (days_passed / total_project_days) * 100
        else:
            progress_percentage = 0
    else:
        progress_percentage = 0

    # Retrieve user details for project members
    project_member_details = []
    member_status = None  # Initialize member_status as None
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_user = Users.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor',
            'online': member_user.online,
        }
        project_member_details.append(member_info)
        member_status = member.status  # Set member_status to the status of the last member

    # Exclude users who are already members of the project
    existing_members = ProjectMembers.objects.filter(project=project, is_deleted=0).values_list('user_id', flat=True)
    clients_profiles = Profile.objects.filter(user_type='Client').exclude(user__id__in=existing_members)
    contractors_profiles = Profile.objects.filter(user_type='Contractor').exclude(user__id__in=existing_members)
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'email_address': profile.user.email,
            'image': profile.profile_picture.url if profile.profile_picture else None,
            'role': profile.user_type 
        }
        user_details.append(user_info)

    open_pmembers = False

    search_query = request.GET.get('search', '').strip()
    if search_query:
        # Filter the list using list comprehension
        user_details = [user for user in user_details if search_query.lower() in user['first_name'].lower()]
        open_pmembers = True

    # Implement pagination (4 user details per page)
    paginator = Paginator(user_details, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        user_details = paginator.page(page_number)
    except (ValueError, EmptyPage):
        projects = paginator.page(1)

    # Fetch unread messages from ChatStatus table
    unread_messages = ChatStatus.objects.filter(user_id=user.id, group=project.groupchat, status=1, is_deleted=0)

    project_tasks = Tasks.objects.filter(project=project, is_deleted=0)

    events = Events.objects.filter(project_id=pk, user=user.id, is_deleted=0)
    pending_tasks = ptasks.count()
    completed_tasks = ctasks.count()
    pending_tasks1 = p1tasks.count()
    completed_tasks1 = c1tasks.count()

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture if profile.profile_picture else None,
        'type': profile.user_type,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'leader_profile': leader_profile,
        'member_status': member_status,
        'user_details': user_details,
        'project_member_details': project_member_details,
        'unread_messages': unread_messages,
        'tasks': ptasks,
        'ctasks': ctasks,
        'p1tasks': p1tasks,
        'c1tasks': c1tasks,
        'events': events,
        'project_tasks': project_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks1': pending_tasks1,
        'completed_tasks1': completed_tasks1,
        'leader_profile': leader_profile,
        'leader_user': leader_user,
        'pending_tasks': pending_tasks,
        'project_membersC': project_membersC,
        'progress_percentage': progress_percentage,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'type': type,
        'open_pmembers': open_pmembers,
    }
    return render(request, 'project-details.html', context)

@login_required
def update_project(request, pk):
    user = request.user
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    profile = user.profile
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    if request.method == 'POST':
        project_name = request.POST['pname']
        start_date = request.POST['sdate']
        end_date = request.POST['edate']
        estimated_budget = request.POST['ebug']
        project_details = request.POST['pdet']
        
        # Update project fields
        project.project_name = project_name
        project.start_date = start_date
        project.end_date = end_date
        project.estimated_budget = estimated_budget
        project.project_details = project_details
        
        # Handle image upload if a new image is provided
        if 'image' in request.FILES:
            profile_picture = request.FILES['image']
            unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
            profile_picture_path = default_storage.save(unique_filename, profile_picture)
            dest_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', unique_filename)

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                project.project_image = 'profile_pictures/' + unique_filename
            except Exception as e:
                messages.error(request, f"Error saving profile picture: {str(e)}")
                return render(request, 'project-details.html', {'project': project})

        # Save the project
        project.save()

        return redirect('project_detail', pk=project.pk)

    # Query for clients and contractors
    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    # Combine clients and contractors into a single list
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'image': profile.profile_picture.url if profile.profile_picture else None,
            'role': 'client' if profile.user_type == 'client' else 'contractor'
        }
        user_details.append(user_info)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'leader_profile': leader_profile,
        'member_status': member.status,
        'user_details': user_details,
    }
    return render(request, 'project-details.html', context)

@login_required
def delete_message(request, pk):
    user = request.user
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    profile = user.profile
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    if request.method == 'POST':
        try:
            message_id = request.POST.get('mid')
            chat_message = get_object_or_404(Chat, pk=message_id)

            # Set the is_deleted flag to 1 for the Chat message
            chat_message.is_deleted = 1
            chat_message.save()
            

            # Set the is_deleted flag to 1 for related ChatStatus entries
            chat_statuses = ChatStatus.objects.filter(chat=chat_message)
            for chat_status in chat_statuses:
                chat_status.is_deleted = 1
                chat_status.status = 0
                chat_status.save()
            logger.info(f"ChatStatus entries for chat message with id {message_id} marked as deleted.")

            return redirect('chat', pk=project.pk)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return redirect('chat', pk=project.pk)

    # Query for clients and contractors
    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    # Combine clients and contractors into a single list
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'role': 'client' if profile.user_type == 'client' else 'contractor'
        }
        user_details.append(user_info)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'leader_profile': leader_profile,
        'user_details': user_details,
    }
    return render(request, 'chat.html', context)

@login_required
def send_message(request, pk):
    user = request.user
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    profile = user.profile
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    if request.method == 'POST':
        # Sending a chat message
        message1 = request.POST.get('message')
        uid = request.POST.get('uid')
        file = request.FILES.get('file')

        chat_file = None
        if file:
            profile_picture = file
            unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
            profile_picture_path = default_storage.save(unique_filename, profile_picture)

            # Move the image to the desired directory under MEDIA_ROOT
            dest_path = os.path.join(settings.MEDIA_ROOT, 'chat_files', unique_filename)

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                chat_file = 'chat_files/' + unique_filename
            except Exception as e:
                messages.error(request, f"Error saving project file: {str(e)}")
                return redirect('chat', pk=project.pk)

        sender_user = User.objects.get(pk=uid)
        logger.info(f"Received message: {message1}")
        message = smart_str(message1)
        logger.info(f"Encoded message: {message}")

        new_chat = Chat.objects.create(
            group=project.groupchat,
            sender_user=sender_user,
            message=message,
            timestamp=timezone.now(),
            is_deleted=0,
            file=chat_file
        )
        new_chat.save()

        # Implementing the trigger logic
        # Get the group chat users excluding the sender
        project_members = ProjectMembers.objects.filter(project=project, is_deleted=0).exclude(user=user)
        logger.info(f"Project members found: {project_members.count()}")

        # Create ChatStatus for each project member
        for project_member in project_members:
            # Check if ChatStatus already exists for this user and new_chat
            existing_status = ChatStatus.objects.filter(
                user_id=project_member.user_id,
                group=new_chat.group,
                chat=new_chat
            ).exists()

            if not existing_status:
                chat_status = ChatStatus.objects.create(
                    chat=new_chat,
                    group=project.groupchat,
                    user_id=project_member.user_id,
                    status=1,
                    is_deleted=0 
                )
                logger.info(f"Chat status created for user: {project_member.user.id}")

        # Check if the authenticated user is the project leader
        if user.id != project.leader_id:
            # Check if ChatStatus already exists for project leader and new_chat
            existing_leader_status = ChatStatus.objects.filter(
                user_id=project.leader_id,
                group=new_chat.group,
                chat=new_chat
            ).exists()

            if not existing_leader_status:
                ChatStatus.objects.create(
                    chat=new_chat,
                    group=project.groupchat,
                    user_id=project.leader_id,
                    status=1,
                    is_deleted=0 
                )
                logger.info(f"Chat status created for project leader: {project.leader_id}")

        return redirect('chat', pk=project.pk)

    # Query for clients and contractors
    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    # Combine clients and contractors into a single list
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'role': 'client' if profile.user_type == 'client' else 'contractor'
        }
        user_details.append(user_info)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'leader_profile': leader_profile,
        'user_details': user_details,
    }
    return render(request, 'chat.html', context)


@login_required
def add_project_member(request, pk):
    user = request.user
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    profile = user.profile
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id) 

    if request.method == 'POST':
        user_id = request.POST['uid']
        leader_id = request.POST['lid']
        user_name = request.POST['uname']
        leader_name = request.POST['lname']
        user_email = request.POST['uemail']

        projectM = ProjectMembers(
            leader_id=leader_id,
            user_name=user_name,
            project_id=project.project_id,
            user_id=user_id,
            created_at=timezone.now(),
            is_deleted=0,
            status = 'Pending',
        )
        projectM.save()

        send_mail(
            'Site Sync: Alert - Project Invitation Notification',
            f'Dear {user_name}, we trust you are well. You have received a project invitation from {leader_name}, on the project {project.project_name}. Kindly login to your account, to get accept/reject the project invitation request.\n\n Thank you for choosing, Site Sync.',
            'sitesync2024@gmail.com',  # Replace with your email
            [user_email],
            fail_silently=False,
        )

        return redirect('project_detail', pk=project.pk)

    project_member_details = []
    member_status = None  # Initialize member_status
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'status': member_profile.status,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)
        # Assign status to member_status, will be the last member's status
        member_status = member_profile.status

    # Query for clients and contractors
    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    # Combine clients and contractors into a single list
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'email_address': profile.user.email,
            'role': 'client' if profile.user_type == 'client' else 'contractor'
        }
        user_details.append(user_info)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'member_status': member.status,
        'leader_profile': leader_profile,
        'user_details': user_details,
    }
    return render(request, 'project-details.html', context)

@login_required
def remove_project_member(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)

    # Retrieve user details for project members
    project_member_details = []
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)

    if request.method == 'POST':
        try:
            uid = request.POST.get('uid')

            # Retrieve the project member to update
            project_member = ProjectMembers.objects.get(user_id=uid)

            # Update the status
            project_member.is_deleted = 1
            project_member.save()

            messages.success(request, 'Project member status updated successfully.')
            # return redirect('project_detail', pk=project.pk)  # Redirect to the project_detail page after successful update

        except ProjectMembers.DoesNotExist:
            messages.error(request, 'Project member not found.')
            # return redirect('project_detail', pk=project.pk)  # Redirect or render an error page as needed

        except Exception as e:
            messages.error(request, f"Error updating project member status: {str(e)}")
            # return redirect('project_detail', pk=project.pk)  # Redirect or render an error page as needed

        # return redirect('project_detail', pk=project.pk)

    # Query for clients and contractors
    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    # Combine clients and contractors into a single list
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'role': 'client' if profile.user_type == 'client' else 'contractor'
        }
        user_details.append(user_info)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'member_status': member.status,
        'leader_profile': leader_profile,
        'user_details': user_details,
    }
    return render(request, 'project-details.html', context)

@login_required
def exit_project(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)

    Bookmarks.objects.filter(item_id__in=project).update(is_deleted=1)

    if request.method == 'POST':
        try:
            uid = request.POST.get('uid')

            # Retrieve the project member to update
            project_member = ProjectMembers.objects.get(user_id=uid)

            # Update the status
            project_member.is_deleted = 1
            project_member.status = 'Exited'
            project_member.save()

            messages.success(request, '')
            # return redirect('project_detail', pk=project.pk)  # Redirect to the project_detail page after successful update

        except ProjectMembers.DoesNotExist:
            messages.error(request, 'Project member not found.')
            # return redirect('project_detail', pk=project.pk)  # Redirect or render an error page as needed

        except Exception as e:
            messages.error(request, f"Error updating project member status: {str(e)}")
            # return redirect('project_detail', pk=project.pk)  # Redirect or render an error page as needed

        # return redirect('project_detail', pk=project.pk)

    # Query for clients and contractors
    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    # Combine clients and contractors into a single list
    users = list(clients_profiles) + list(contractors_profiles)

    # Retrieve user details from User model
    user_details = []
    for profile in users:
        user_info = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'phone_number': profile.phone_number,
            'id': profile.user.id,
            'role': 'client' if profile.user_type == 'client' else 'contractor'
        }
        user_details.append(user_info)

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'member_status': member.status,
        'leader_profile': leader_profile,
        'user_details': user_details,
    }
    return redirect('client')

@login_required
def client(request):
    user = request.user
    profile = user.profile
    type = profile.user_type
    now = date.today()
    today = now.strftime('%Y-%m-%d')

    # Fetch projects where the current user is the leader or a member
    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Project', user_id=request.user.id)
    bookmarked_project_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_projects = Projects.objects.filter(project_id__in=bookmarked_project_ids)
    all_projects = (leader_projects | member_projects | bookmarked_projects).distinct()

    # Calculate counts for each category
    all_projects_count = all_projects.count()
    active_projects_count = all_projects.filter(project_status='Active').count()
    completed_projects_count = all_projects.filter(project_status='Completed').count()
    trash_projects_count = trash_projects.count()
    bookmark_projects_count = bookmarked_projects.count()
    # Initialize filter information
    date_filter_display = "All Time"
    status_filter_display = "All Projects"

    search_query = request.GET.get('search', '').strip()
    if search_query:
        all_projects = all_projects.filter(project_name__icontains=search_query)

    # Apply date filtering
    date_filter = request.GET.get('date_filter')
    if date_filter:
        if date_filter == 'today':
            all_projects = all_projects.filter(created_at__date=current_date)
            date_filter_display = "Today"
        elif date_filter == 'this_week':
            start_of_week = current_date - timedelta(days=current_date.weekday())
            all_projects = all_projects.filter(created_at__date__gte=start_of_week)
            date_filter_display = "This Week"
        elif date_filter == 'this_month':
            all_projects = all_projects.filter(created_at__year=current_date.year, created_at__month=current_date.month)
            date_filter_display = "This Month"
        elif date_filter == 'this_year':
            all_projects = all_projects.filter(created_at__year=current_date.year)
            date_filter_display = "This Year"

    # Apply status filtering
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'active':
        projects = all_projects.filter(project_status='Active')
        status_filter_display = "Active Projects"
    elif filter_type == 'completed':
        projects = all_projects.filter(project_status='Completed')
        status_filter_display = "Completed Projects"
    elif filter_type == 'bookmarked':
        projects = bookmarked_projects
        status_filter_display = "Bookmarked Projects"
    else:
        projects = all_projects
        status_filter_display = "All Projects"

    # Implement pagination (4 projects per page)
    paginator = Paginator(projects, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        projects = paginator.page(page_number)
    except (ValueError, EmptyPage):
        projects = paginator.page(1)

    unread_chat_counts = {}
    pending_tasks_counts = {}
    progress_percentages = {}

    all_unread_chats = []
    all_pending_tasks = []

  # Calculate unread chat statuses and pending tasks for each project
    for project in projects:
        try:
            group_chat = GroupChat.objects.get(project=project)
            chats = Chat.objects.filter(group_id=group_chat.group_id)
            all_unread_chats = ChatStatus.objects.filter(
                user_id=profile.user_id,
                group_id=group_chat.group_id,
                status=1,
                is_deleted=0
            )
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )
            unread_chat_counts[project.project_id] = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_chat_counts[project.project_id] = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0
        ).exclude(
            task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
        )
        pending_tasks_counts[project.project_id] = all_pending_tasks.count()

        # Calculate progress value
        total_days = (project.end_date - project.start_date).days
        days_left = (project.end_date - now).days
        progress_percentage = ((total_days - days_left) / total_days) * 100 if total_days > 0 else 0
        progress_percentages[project.project_id] = progress_percentage

    # Count pending project invitations for the current user
    pending_project_count = ProjectMembers.objects.filter(user_id=profile.user_id, status='Pending').count()

    # Fetch pending projects where the current user is a member
    pending_project_members = ProjectMembers.objects.filter(user_id=profile.user_id, status='Pending')
    pending_projects = Projects.objects.filter(project_id__in=pending_project_members.values_list('project_id', flat=True))

    # Fetch all users who are clients or contractors
    clients = User.objects.filter(profile__user_type='client')
    contractors = User.objects.filter(profile__user_type='contractor')

    # Optionally, combine them into a single list
    users = list(clients) + list(contractors)

    if request.method == 'POST':
        action = request.POST.get('action')
        action1 = request.POST.get('action1')
        selected_project_ids = request.POST.getlist('selected_projects')
        selected_project_id = request.POST.get('selected_project')

        if action == 'delete':
            user_id = request.user.id
            projects = Projects.objects.filter(project_id__in=selected_project_ids)
            
            for project in projects:
                if project.leader_id != user_id:
                    messages.error(request, "You do not have permission to delete one or more of the selected projects.")
                    return redirect('client')

            projects.update(is_deleted=1)
            messages.success(request, 'Selected projects have been deleted.')
            return redirect('client')
        elif action == 'bookmark':
            for project_id in selected_project_ids:
                bookmarkP = Bookmarks(
                    item_type='Project',
                    item_id=project_id,
                    user_id=request.user.id,
                    project_id=0,
                    timestamp=timezone.now(),
                    is_deleted=0
                )
                bookmarkP.save()
            messages.success(request, '')
            return redirect('client')
        elif action == 'unbookmark':
            Bookmarks.objects.filter(item_id__in=selected_project_ids, item_type='Project', user_id=request.user.id).update(is_deleted=1)
            messages.success(request, '')
            return redirect('client')
        elif action1 == 'bookmark1':
            bookmarkP = Bookmarks(
                item_type='Project',
                item_id=selected_project_id,
                user_id=request.user.id,
                project_id=0,
                timestamp=timezone.now(),
                is_deleted=0
            )
            bookmarkP.save()
            messages.success(request, '')
            return redirect('client')
        elif action1 == 'unbookmark1':
            Bookmarks.objects.filter(item_id__in=selected_project_id, item_type='Project', user_id=request.user.id).update(is_deleted=1)
            messages.success(request, '')
            return redirect('client')
        elif action == 'delete1':
            user_id = request.user.id
            projects = Projects.objects.filter(project_id__in=selected_project_ids)
            
            for project in projects:
                if project.leader_id != user_id:
                    messages.error(request, "You do not have permission to delete one or more of the selected projects.")
                    return redirect('client')

            projects.update(is_deleted=2)
            messages.success(request, 'Selected projects have been deleted.')
            return redirect('client')
        elif action == 'restore':
            Projects.objects.filter(project_id__in=selected_project_ids).update(is_deleted=0)
            messages.success(request, '')
            return redirect('client')
        else:
            pname = request.POST.get('pname')
            sdate = request.POST.get('sdate')
            edate = request.POST.get('edate')
            ebug = request.POST.get('ebug')
            pdet = request.POST.get('pdet')
            image = request.FILES.get('image')

            # Check if all required form inputs are present
            if not all([pname, sdate, edate, ebug, pdet]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'dashboard.html', {'fname': user.first_name, 'image': profile.profile_picture.url if profile.profile_picture else None, 'MEDIA_URL': settings.MEDIA_URL, 'day': today})

            try:
                start_date = date.fromisoformat(sdate)
                end_date = date.fromisoformat(edate)
                total_days = (end_date - start_date).days
                actual_expenditure = 0
                balance = float(ebug)
                project_status = 'Active'
                leader_id = user.id  # Use the logged-in user's ID
                is_deleted = 0

                # Save the image if provided
                project_image = None
                if image:
                    profile_picture = image
                    unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
                    profile_picture_path = default_storage.save(unique_filename, profile_picture)

                    # Move the image to the desired directory under MEDIA_ROOT
                    dest_path = os.path.join(settings.MEDIA_ROOT, 'project_images', unique_filename)

                    try:
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                        project_image = 'project_images/' + unique_filename
                    except Exception as e:
                        messages.error(request, f"Error saving project image: {str(e)}")
                        return render(request, 'dashboard.html', {'fname': user.first_name, 'image': profile.profile_picture.url if profile.profile_picture else None, 'MEDIA_URL': settings.MEDIA_URL, 'day': today})

                # Save the project details
                project1 = Projects(
                    leader_id=leader_id,
                    project_name=pname,
                    project_details=pdet,
                    project_image=project_image,
                    created_at=timezone.now(),
                    start_date=start_date,
                    end_date=end_date,
                    total_days=total_days,
                    estimated_budget=balance,
                    actual_expenditure=actual_expenditure,
                    balance=balance,
                    project_status=project_status,
                    is_deleted=is_deleted
                )
                project1.save()
                group_chat = GroupChat(
                leader_id=leader_id,
                project=project1,
                group_name=pname,  
                is_deleted=is_deleted,
                )
                group_chat.save()
                messages.success(request, '')
                return redirect('client')  # Adjust the redirect as needed

            except Exception as e:
                messages.error(request, f"Error processing form: {str(e)}")
                return render(request, 'dashboard.html', {'fname': user.first_name, 'image': profile.profile_picture.url if profile.profile_picture else None, 'MEDIA_URL': settings.MEDIA_URL, 'day': today})

        # Initialize member status as None
        member_status = None
        if projects.exists():
            # Fetch the first project and check for members
            first_project = projects.first()
            project_members = ProjectMembers.objects.filter(project=first_project, is_deleted=0)
            if project_members.exists():
                # Set member status based on the first member found
                member_status = project_members.first().status

    context = {
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'now': now, 
        'projects': projects,
        'filter_type': filter_type,
        'trash_projects': trash_projects,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'progress_percentages': progress_percentages,
        'all_projects_count': all_projects_count,
        'active_projects_count': active_projects_count,
        'bookmark_projects_count': bookmark_projects_count,
        'status_filter_display': status_filter_display,
        'date_filter_display': date_filter_display,
        'completed_projects_count': completed_projects_count,
        'trash_projects_count': trash_projects_count,
        'type': type,
        'pending_projects': pending_projects,
        'pending_project_count': pending_project_count,
        'bookmarked_project_ids': bookmarked_project_ids,
    }
    messages.info(request, "")
    return render(request, 'dashboard.html', context)

@login_required
def update_project_member(request):
    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')

    # Fetch projects where the current user is the leader
    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)

    # Fetch projects where the current user is a member
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True)
    )

    # Combine both queries using OR condition
    projects = leader_projects | member_projects

    # Count the number of projects where the current user is the leader
    project_count = projects.count()

    # Count pending project invitations for the current user
    pending_project_count = ProjectMembers.objects.filter(user_id=profile.user_id, status='Pending').count()

    # Fetch pending projects where the current user is a member
    pending_project_members = ProjectMembers.objects.filter(user_id=profile.user_id, status='Pending')
    pending_projects = Projects.objects.filter(project_id__in=pending_project_members.values_list('project_id', flat=True))

    # Fetch all users who are clients or contractors
    clients = User.objects.filter(profile__user_type='client')
    contractors = User.objects.filter(profile__user_type='contractor')

    # Optionally, combine them into a single list
    users = list(clients) + list(contractors)

    if request.method == 'POST':
        try:
            pid = request.POST.get('pid')
            stat = request.POST.get('stat')

            # Retrieve the project member to update
            project_member = ProjectMembers.objects.get(project_id=pid, status='Pending')

            # Update the status
            project_member.status = stat
            project_member.save()

            messages.success(request, '')
            return redirect('client')  # Redirect to the client page after successful update

        except ProjectMembers.DoesNotExist:
            messages.error(request, 'Project member not found.')
            return redirect('client')  # Redirect or render an error page as needed

        except Exception as e:
            messages.error(request, f"Error updating project member status: {str(e)}")
            return redirect('client')  # Redirect or render an error page as needed

    context = {
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'users': users,
        'type': profile.user_type,
        'project_count': project_count,
        'pending_projects': pending_projects,
        'pending_project_count': pending_project_count,
    }
    messages.info(request, "")
    return render(request, 'dashboard.html', context)

def prototype(request):
    return render(request, 'presentation.html')

def validate_password(password):
    if (len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'[0-9]', password) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        return True
    return False

from django.core.mail import send_mail
import uuid
import os

def signup(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        # Check if user with this email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email address already in use. Please choose a different one.")
            return render(request, 'register.html')

        password = request.POST.get('password')
        if not validate_password(password):
            messages.error(request, "Password must be at least 8 characters long, contain uppercase and lowercase letters, numbers, and symbols.")
            return render(request, 'register.html')

        # Create new user
        user = User.objects.create_user(username=email, email=email, first_name=request.POST.get('fname'), password=password)

        # Additional profile information
        profile = Profile.objects.get(user=user)
        profile.phone_number = request.POST.get('phone')
        profile.gender = request.POST.get('gen')
        profile.user_type = request.POST.get('type')
        profile.created_at = timezone.now()
        profile.updated_at = None

        if 'image' in request.FILES:
            profile_picture = request.FILES['image']
            unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
            profile_picture_path = default_storage.save(unique_filename, profile_picture)

            # Move the image to the desired directory under MEDIA_ROOT
            dest_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', unique_filename)

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                profile.profile_picture = 'profile_pictures/' + unique_filename
                profile.save()
            except Exception as e:
                messages.error(request, f"Error saving profile picture: {str(e)}")
                return render(request, 'register.html')

        profile.save()
        Users.objects.create(
            user_id=profile.user_id,
            email_address=email,
            created_at=timezone.now(),
            user_type=profile.user_type,
            is_deleted=0,
            online=0,
            gender=profile.gender,
            phone_number=profile.phone_number  
        )
        messages.success(request, "")

        # Generate OTP
        otp, created = OTP.objects.get_or_create(user=user)
        otp.generate_otp()

        # Send OTP to user's email
        send_mail(
            'Site Sync: OTP Code',
            f'Your OTP code is {otp.otp_code}. \n\n Thank you for choosing Site Sync.',
            'sitesync2024@gmail.com',  # Replace with your email
            [user.email],
            fail_silently=False,
        )

        # Store the user ID in session to use during OTP verification
        request.session['user_id'] = user.id
        messages.success(request, 'OTP has been sent to your email. Please verify to complete the signup process.')
        return redirect('verify_otp')

    return render(request, 'register.html')

def google_signup(request):
    strategy = load_strategy(request)
    # Strategy will handle the Google OAuth sign-up flow and redirect
    return redirect(strategy.get_setting('LOGIN_REDIRECT_URL'))

@login_required
def complete_profile(request):
    if request.method == "POST":
        profile = request.user.profile
        profile.phone_number = request.POST.get('phone')
        profile.gender = request.POST.get('gender')
        profile.user_type = request.POST.get('user_type')
        profile.save()

        # Authenticate and log in the user
        login(request, request.user)

        # Redirect based on user type
        if request.user.profile.user_type == 'Admin':
            return redirect('admin1')  # Ensure 'admin1' matches your URL name
        elif request.user.profile.user_type == 'Client':
            return redirect('client')  # Ensure 'client' matches your URL name
        elif request.user.profile.user_type == 'Contractor':
            return redirect('client')  # Ensure 'contractor' matches your URL name
        else:
            return redirect('home')  # Ensure 'home' matches your URL name

    return render(request, 'complete_profile.html')

@login_required
def profile(request):
    user = request.user
    profile = user.profile
    user_type = profile.user_type
    user_id = profile.user_id

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    unread_chat_counts = {}
    pending_tasks_counts = {}

    all_unread_chats = []
    all_pending_tasks = []

    # Calculate unread chat statuses and pending tasks for each project
    for project in projects:
        try:
            group_chat = GroupChat.objects.get(project=project)
            chats = Chat.objects.filter(group_id=group_chat.group_id)
            all_unread_chats = ChatStatus.objects.filter(
                user_id=profile.user_id,
                group_id=group_chat.group_id,
                status=1,
                is_deleted=0
            )
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )
            unread_chat_counts[project.project_id] = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_chat_counts[project.project_id] = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0
        ).exclude(
            task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
        )
        pending_tasks_counts[project.project_id] = all_pending_tasks.count()

    if request.method == "POST":
        email = request.POST.get('email')

        # Check if the email is being changed and if it already exists
        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, "Email address already in use. Please choose a different one.")
            return redirect('profile')

        password = request.POST.get('password')
        if password and not validate_password(password):
            messages.error(request, "Password must be at least 8 characters long, contain uppercase and lowercase letters, numbers, and symbols.")
            return redirect('profile')

        # Update user details
        user.first_name = request.POST.get('fname')
        user.email = email
        if password:
            user.set_password(password)
        user.save()

        # Update profile information
        profile.phone_number = request.POST.get('phone')
        profile.updated_at = timezone.now()

        if 'image' in request.FILES:
            profile_picture = request.FILES['image']
            unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
            profile_picture_path = default_storage.save(unique_filename, profile_picture)
            dest_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', unique_filename)
            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                profile.profile_picture = 'profile_pictures/' + unique_filename
            except Exception as e:
                messages.error(request, f"Error saving profile picture: {str(e)}")
                return redirect('profile')

        profile.save()
        
        messages.success(request, "")
        
        # If the password was changed, update the session to prevent logout
        if password:
            update_session_auth_hash(request, user)
        
        return redirect('profile')

    context = {
        'user': user,
        'profile': profile,
        'type': user_type,
        'uid': user_id,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
    }
    return render(request, 'profile.html', context)

def verify_otp(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        user_id = request.session.get('user_id')
        
        if user_id:
            try:
                # Get the OTP entry for the user
                otp = OTP.objects.get(user_id=user_id, otp_code=otp_code, used=False)

                # Check if OTP is valid (you can add additional checks here if needed)
                # if otp.created_at >= timezone.now() - timedelta(minutes=15):
                if otp:
                    otp.used = True  # Mark the OTP as used
                    otp.save()

                    # Get the user associated with the OTP
                    user = otp.user

                    # Perform login with specified backend
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                    Users.objects.filter(email_address=user).update(online=1)

                    # Redirect based on user type
                    if hasattr(user, 'profile'):
                        if user.profile.user_type == 'Admin':
                            return redirect('admin1')
                        elif user.profile.user_type == 'Client':
                            return redirect('client')
                        elif user.profile.user_type == 'Contractor':
                            return redirect('client')
                    else:
                        return redirect('home')

                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return redirect('verify_otp')

            except OTP.DoesNotExist:
                messages.error(request, 'Invalid OTP.')
                return redirect('verify_otp')

    return render(request, 'otp.html')

def signin(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # Could be email or phone number
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            # Log in the user
            login(request, user)

            # Set the user as online
            Users.objects.filter(email_address=user.email).update(online=1)

            # Redirect based on user type
            if hasattr(user, 'profile'):
                if user.profile.user_type == 'Admin':
                    return redirect('admin1')  # Ensure 'admin1' matches your URL name
                elif user.profile.user_type == 'Client':
                    return redirect('client')  # Ensure 'client' matches your URL name
                elif user.profile.user_type == 'Contractor':
                    return redirect('client')  # Ensure 'contractor' matches your URL name
                else:
                    return redirect('home')  # Default redirect if user type is not recognized
            else:
                return redirect('home')  # Redirect if the user has no profile

        else:
            # Authentication failed
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')

    return render(request, 'login.html')

@login_required
def delete_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('uid')
        user = get_object_or_404(User, pk=user_id)
        user.is_active = False  # Soft delete the user by deactivating the account
        user.save()
        messages.success(request, 'User has been deactivated successfully.')
    return redirect('user_logout')

def user_logout(request):
    user = request.user
    Users.objects.filter(email_address=user.email).update(online=0)
    logout(request)
    return redirect('/')

def generate_otp():
    return random.randint(100000, 999999)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            otp = generate_otp()
            otp_entry, created = OTP.objects.get_or_create(user=user)
            otp_entry.otp_code = otp
            otp_entry.save()
            send_mail(
                'Site Sync: Alert - Password Reset OTP',
                f'Your OTP code is {otp}. \n\n Thank you for choosing, Site Sync.',
                'sitesync2024@gmail.com',  # Replace with your email
                [user.email],
                fail_silently=False,
            )
            request.session['user_id'] = user.id
            messages.success(request, 'OTP has been sent to your email.')
            return redirect('verify_otp1')
        else:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'forgot_password.html')

def verify_otp1(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        user_id = request.session.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        otp = OTP.objects.filter(user=user, otp_code=otp_code).first()

        if otp:
            # OTP is valid, proceed to password reset
            return redirect('reset_password', uidb64=urlsafe_base64_encode(force_bytes(user.pk)), token=default_token_generator.make_token(user))
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html')

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password == confirm_password:
                if not validate_password(password):
                    messages.error(request, "Password must be at least 8 characters long, contain uppercase and lowercase letters, numbers, and symbols.")
                else:
                    user.set_password(password)
                    user.save()
                    messages.success(request, 'Your password has been reset successfully.')
                    return redirect('signin')
            else:
                messages.error(request, 'Passwords do not match.')

        return render(request, 'reset_password.html')
    else:
        messages.error(request, 'The reset link is invalid, possibly because it has already been used.')
        return redirect('signin')