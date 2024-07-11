from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Users, OTP, Profile, Projects, User, ProjectMembers, Chat, GroupChat, ChatStatus, Resources, Events, Tasks, Transactions
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

@login_required
def resources(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    resources = Resources.objects.filter(project_id=pk, is_deleted=0)
    resource_count = resources.count()
    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'type': profile.user_type,
        'resources': resources,
        'leader_profile': leader_profile,
        'resource_count': resource_count,
    }
    return render(request, 'resources.html', context)

@login_required
def add_resource(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        file = request.FILES.get('resource_file')
        chat_file = None
        if file:
            profile_picture = file
            unique_filename = str(uuid.uuid4()) + os.path.splitext(profile_picture.name)[1]
            profile_picture_path = default_storage.save(unique_filename, profile_picture)

            # Move the image to the desired directory under MEDIA_ROOT
            dest_path = os.path.join(settings.MEDIA_ROOT, 'project_resources', unique_filename)

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                chat_file = 'project_resources/' + unique_filename
            except Exception as e:
                messages.error(request, f"Error saving project file: {str(e)}")
                return redirect('resources', pk=pk)

        resource = Resources(
            user=request.user,
            project=project,
            resource_name=request.POST['resource_name'],
            resource_details=request.POST['resource_details'],
            resource_type=request.POST['resource_type'],
            resource_status='All',
            resource_directory = chat_file,
            is_deleted = 0,
            status='Pending',
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

    # print(f"User ID: {user.id}")
    # print(f"Project ID: {pk}")
    # print(f"Number of tasks: {tasks.count()}")
    # print(f"Number of pending tasks: {ptasks.count()}")
    # print(f"Number of completed tasks: {ctasks.count()}")

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
    project.is_deleted = 1
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
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

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
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)
        member_status = member.status  # Set member_status to the status of the last member

    # Exclude users who are already members of the project
    existing_members = ProjectMembers.objects.filter(project=project, is_deleted=0).values_list('user_id', flat=True)
    clients_profiles = Profile.objects.filter(user_type='Client').exclude(user__id__in=existing_members)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user__id__in=existing_members)
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
        'image1': profile.profile_picture.url if profile.profile_picture else None,
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
        'pending_tasks': pending_tasks,
        'project_membersC': project_membersC,
        'progress_percentage': progress_percentage,
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
def client(request):
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

    # Initialize unread chat counts and pending tasks dictionaries
    unread_chat_counts = {}
    pending_tasks_counts = {}
    progress_values = {}
    progress_percentages = {}

    # Calculate unread chat statuses and pending tasks for each project
    for project in projects:
        try:
            group_chat = GroupChat.objects.get(project=project)
            unread_count = ChatStatus.objects.filter(
                user_id=profile.user_id,
                group_id=group_chat.group_id,
                status=1,
                is_deleted=0,
            ).count()
            unread_chat_counts[project.project_id] = unread_count
        except GroupChat.DoesNotExist:
            unread_chat_counts[project.project_id] = 0

        # Count pending tasks
        pending_tasks_count = Tasks.objects.filter(
            project=project,
            is_deleted=0
        ).exclude(
            task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
        ).count()
        pending_tasks_counts[project.project_id] = pending_tasks_count

        # Calculate progress value
        total_days = (project.end_date - project.start_date).days
        days_left = (project.end_date - now).days
        progress_percentage = ((total_days - days_left) / total_days) * 100 if total_days > 0 else 0
        progress_percentages[project.project_id] = progress_percentage

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
        pname = request.POST.get('pname')
        sdate = request.POST.get('sdate')
        edate = request.POST.get('edate')
        ebug = request.POST.get('ebug')
        pdet = request.POST.get('pdet')
        image = request.FILES.get('image')

        # Check if all required form inputs are present
        if not all([pname, sdate, edate, ebug, pdet]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'client.html', {'fname': user.first_name, 'image': profile.profile_picture.url if profile.profile_picture else None, 'MEDIA_URL': settings.MEDIA_URL, 'day': today})

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
            project = Projects(
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
                is_deleted=is_deleted,
            )
            project.save()
            messages.success(request, 'Project created successfully.')
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
        'users': users,
        'type': profile.user_type,
        'project_count': project_count,
        'projects': projects,
        'pending_projects': pending_projects,
        'pending_project_count': pending_project_count,
        'unread_chat_counts': unread_chat_counts,  
        'pending_tasks_counts': pending_tasks_counts,  
        'progress_values': progress_values, 
        'progress_percentages': progress_percentages, 
        'member_status': member_status,  
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

            messages.success(request, 'Project member status updated successfully.')
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

        # Authenticate and log in the user
        auth_user = authenticate(request, username=email, password=password)
        if auth_user is not None:
            login(request, auth_user)
            if hasattr(request.user, 'profile'):
                if request.user.profile.user_type == 'Admin':
                    return redirect('admin1')  # Ensure 'admin' matches your URL name
                elif request.user.profile.user_type == 'Client':
                            return redirect('client')  # Ensure 'client' matches your URL name
                elif request.user.profile.user_type == 'Contractor':
                            return redirect('client')  # Ensure 'contractor' matches your URL name
                else:
                        # Handle cases where profile doesn't exist
                    return redirect('home')  # Ensure 'home' matches your URL name
        else:
            messages.error(request, 'Failed to log in. Please try again.')
            return render(request, 'login.html')

    return render(request, 'register.html')

def profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        email = request.POST.get('email')

        # Check if the email is being changed and if it already exists
        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, "Email address already in use. Please choose a different one.")
            return render(request, 'profile.html')

        password = request.POST.get('password')
        if password and not validate_password(password):
            messages.error(request, "Password must be at least 8 characters long, contain uppercase and lowercase letters, numbers, and symbols.")
            return render(request, 'profile.html')

        # Update user details
        user.email = email
        user.first_name = request.POST.get('fname')
        if password:
            user.set_password(password)
        user.save()

        # Update profile information
        profile.phone_number = request.POST.get('phone')
        profile.gender = request.POST.get('gen')
        profile.user_type = request.POST.get('type')
        profile.updated_at = timezone.now()

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
                return render(request, 'profile.html')

        profile.save()

        # Update or create entry in Users model
        user_record, created = Users.objects.update_or_create(
            user_id=profile.user_id,
            defaults={
                'email_address': email,
                'updated_at': timezone.now(),
                'user_type': profile.user_type
            }
        )

        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    context = {
        'user': user,
        'profile': profile,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
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
        user_timezone = request.POST.get('timezone', 'UTC')

        user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            otp, created = OTP.objects.get_or_create(user=user)
            otp.generate_otp()  # Regenerate OTP for existing or new entry

            send_mail(
                'Site Sync: OTP Code',
                f'Your OTP code is {otp.otp_code}. \n\n Thank you for choosing, Site Sync.',
                'sitesync2024@gmail.com',  # Replace with your email
                [user.email],
                fail_silently=False,
            )

            request.session['user_id'] = user.id
            messages.success(request, 'OTP has been sent to your email.')
            return redirect('verify_otp')

        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')

    return render(request, 'login.html')

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False  # Soft delete the user by deactivating the account
    user.save()
    messages.success(request, 'User has been deactivated successfully.')
    return redirect('user_logout')

def user_logout(request):
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