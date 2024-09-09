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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum, Count, F, Value
from django.db.models import Subquery, OuterRef
from django.db.models.functions import Concat
from django.http import HttpResponseBadRequest
import json
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Create your views here.

def tasks1(request, project_id):
    # Retrieve tasks for the specific project
    tasks = Tasks.objects.filter(project_id=project_id)

    task_data = []
    for task in tasks:
        # Handle many-to-many members
        members_info = ', '.join(
            f"{member.first_name} ({member.profile.user_type})" for member in task.member.all()
        )

        dependencies = ','.join(str(dep.task_id) for dep in task.dependant_tasks.all())

        if task.task_status in ['Completed Early', 'Completed Late', 'Completed Today']:
            expected_percentage = 100.0
        else:
            expected_percentage = task.expected_percentage_complete

        task_data.append([
            str(task.task_id),  # Task ID
            task.task_name,  # Task Name
            members_info,  # Resource
            task.task_given_date.strftime('%Y-%m-%d'),  # Start Date
            task.task_due_date.strftime('%Y-%m-%d'),  # End Date
            (task.task_due_date - task.task_given_date).days,  # Duration
            expected_percentage,  # Percent Complete
            # ', '.join(str(dep.id) for dep in task.dependant_tasks.all()) 
            str(dependencies), # Dependencies
        ])

    # Return JSON response
    return JsonResponse({'tasks': task_data})

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
    user_id = profile.user_id
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    resources = Resources.objects.filter(project_id=pk, is_deleted=0)
    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Resource', project_id=project.project_id, user_id=request.user.id)
    bookmarked_resources_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_resources = Resources.objects.filter(resource_id__in=bookmarked_resources_ids)
    all_resources = (resources | bookmarked_resources).distinct()
    bookmark_resources_count = bookmarked_resources.count()
    trash_resources = Resources.objects.filter(project_id=pk, is_deleted=1, user_id=user_id)    
    resource_count = all_resources.count()
    video_count = all_resources.filter(resource_type='Video').count()
    document_count = all_resources.filter(resource_type='Document').count()
    audio_count = all_resources.filter(resource_type='Audio').count()
    image_count = all_resources.filter(resource_type='Image').count()    
    trash_resources_count = trash_resources.count()

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    now = timezone.now() 

    unread_chat_counts = {}
    pending_tasks_counts = {}

    all_unread_chats = []
    all_pending_tasks = []

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project1,
            is_deleted=0,
            task_status='Ongoing'
        )
        pending_tasks_counts = all_pending_tasks.count()

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
                        messages.success(request, '')
                    except ValueError:
                        messages.error(request, f'Invalid resource ID: {resource_id}.')
                        return HttpResponseBadRequest(f'Invalid resource ID: {resource_id}')
            else:
                messages.error(request, '')
                return HttpResponseBadRequest('No resources selected')
        
        elif action == 'unbookmark':
            if selected_resource_ids:
                Bookmarks.objects.filter(
                    item_id__in=selected_resource_ids,
                    item_type='Resource',
                    user_id=request.user.id
                ).update(is_deleted=1)
                messages.success(request, '')
            else:
                messages.error(request, '')
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
                    messages.success(request, '')
                except ValueError:
                    messages.error(request, '')
            else:
                messages.error(request, '')

        elif action1 == 'unbookmark1':
            if selected_resource_id:
                try:
                    item_id = int(selected_resource_id)
                    Bookmarks.objects.filter(
                        item_id=item_id,
                        item_type='Resource',
                        user_id=request.user.id
                    ).update(is_deleted=1)
                    messages.success(request, '')
                except ValueError:
                    messages.error(request, '')
            else:
                messages.error(request, '')

        elif action1 == 'delete1':
            if selected_resource_ids:
                Resources.objects.filter(resource_id__in=selected_resource_ids).update(is_deleted=2)
                messages.success(request, '')
            else:
                messages.error(request, '')

        elif action == 'delete':
            if selected_resource_ids:
                Resources.objects.filter(resource_id__in=selected_resource_ids).update(is_deleted=1)
                Bookmarks.objects.filter(
                    item_id__in=selected_resource_ids,
                    item_type='Resource',
                    user_id=request.user.id
                ).update(is_deleted=1)
                messages.success(request, '')
            else:
                messages.error(request, '')
        
        elif action == 'restore':
            if selected_resource_ids:
                Resources.objects.filter(resource_id__in=selected_resource_ids).update(is_deleted=0)
                messages.success(request, '')
            else:
                messages.error(request, '')

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
        'now': now,
        'now': localtime(now),
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
        'unread_count': unread_count,
    }
    return render(request, 'resources.html', context)

@login_required
def add_resource(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        file = request.FILES.get('resource_file')
        chat_file = None
        file_size = None
        file_extension = None

        if file:
            profile_picture = file
            file_extension = os.path.splitext(profile_picture.name)[1]  # Get the file extension
            unique_filename = str(uuid.uuid4()) + file_extension
            profile_picture_path = default_storage.save(unique_filename, profile_picture)

            # Move the file to the desired directory under MEDIA_ROOT
            dest_path = os.path.join(settings.MEDIA_ROOT, 'project_resources', unique_filename)

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(os.path.join(settings.MEDIA_ROOT, profile_picture_path), dest_path)
                chat_file = 'project_resources/' + unique_filename
                
                # Get file size in kilobytes (KB) or megabytes (MB) or gigabytes (GB)
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

        # Append the file extension to the resource name
        resource_name_with_extension = request.POST['resource_name'] + file_extension

        resource = Resources(
            user=request.user,
            project=project,
            resource_name=resource_name_with_extension,
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
    resource.deleted_at = timezone.now()
    resource.save()
    Bookmarks.objects.filter(
        item_id=resource_id,
        item_type='Resource',
        user_id=request.user.id
    ).update(is_deleted=1)
    return redirect('resources', pk=pk)

@login_required
def delete_resources(request, pk=None):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_resource_ids = json.loads(request.POST.get('selected_resource_ids', '[]'))

        if action == 'delete':
            if selected_resource_ids:
                Resources.objects.filter(resource_id__in=selected_resource_ids).update(is_deleted=1, deleted_at=timezone.now())
                Bookmarks.objects.filter(
                    item_id__in=selected_resource_ids,
                    item_type='Resource',
                    user_id=request.user.id
                ).update(is_deleted=1)
                messages.success(request, '')
            else:
                messages.error(request, '')

    return redirect('resources', pk=pk)


@login_required
def restore_resource(request, pk, resource_id):
    resource = get_object_or_404(Resources, pk=resource_id, project__pk=pk)
    resource.is_deleted = 0
    resource.save()
    return redirect('resources', pk=pk)

@login_required
def hide_resource(request, pk, resource_id):
    get_object_or_404(Resources, pk=resource_id, project__pk=pk).delete()
    return redirect('resources', pk=pk)

@login_required
def restore_transaction(request, pk, transaction_id):
    transactions = get_object_or_404(Transactions, pk=transaction_id, project__pk=pk)
    transactions.is_deleted = 0
    transactions.save()
    project = get_object_or_404(Projects, pk=pk)
    project.estimated_budget -= transactions.total_transaction_price
    project.actual_expenditure += transactions.total_transaction_price 
    project.balance = project.estimated_budget - project.actual_expenditure 
    project.save()
    return redirect('transactions', pk=pk)

@login_required
def hide_transaction(request, pk, transaction_id):
    get_object_or_404(Transactions, pk=transaction_id, project__pk=pk).delete()
    return redirect('transactions', pk=pk)

@login_required
def add_transaction(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        tp = float(request.POST['transaction_price']) * int(request.POST['transaction_quantity'])

    newprice = project.balance - tp
    if newprice > 0:
        project.actual_expenditure = tp
        project.balance = project.estimated_budget - project.actual_expenditure 
        project.save()

        transaction = Transactions(
            user=request.user,
            project=project,
            transaction_name=request.POST['transaction_name'],
            transaction_details=request.POST['transaction_details'],
            transaction_price=float(request.POST['transaction_price']),
            transaction_quantity=int(request.POST['transaction_quantity']),
            transaction_type=request.POST['transaction_type'],
            transaction_category=request.POST['transaction_category'],            
            total_transaction_price=float(request.POST['transaction_price']) * int(request.POST['transaction_quantity']),
            created_at=timezone.now(),
            transaction_status='Completed',
            is_deleted=0
        )
        transaction.save()

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
    Bookmarks.objects.filter(
        item_id=transaction_id,
        item_type='Transaction',
        user_id=request.user.id
    ).update(is_deleted=1)
    transactions.is_deleted = 1
    transactions.deleted_at = timezone.now()
    transactions.save()
    return redirect('transactions', pk=pk)

@login_required
def transactions(request, pk):

    user = request.user
    profile = user.profile
    user_id = profile.user_id
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    transactions1 = Transactions.objects.filter(project_id=pk, is_deleted=0)
    transactions1_count = transactions1.count()
    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Transaction', project_id=project.project_id, user_id=request.user.id)
    bookmarked_transactions_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_transactions = Transactions.objects.filter(transaction_id__in=bookmarked_transactions_ids)
    all_transactions = (transactions1 | bookmarked_transactions).distinct()
    bookmark_transactions_count = bookmarked_transactions.count()
    trash_transactions = Transactions.objects.filter(project_id=pk, is_deleted=1,user_id=project.leader_id)    
    transactions_count = all_transactions.count()
    internal_count = all_transactions.filter(transaction_category='Internal').count()
    external_count = all_transactions.filter(transaction_category='External').count() 
    trash_transactions_count = trash_transactions.count()

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
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
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project1,
            is_deleted=0,
            task_status='Ongoing'
        )
        pending_tasks_counts = all_pending_tasks.count()

    date_filter_display = "All Time"
    status_filter_display = "All Transactions"

    if request.method == "POST":
        action = request.POST.get('action')
        action1 = request.POST.get('action1')
        selected_transaction_ids = request.POST.getlist('selected_transactions')  # Handles multiple selections
        selected_transaction_id = request.POST.get('selected_transaction')  # Handles single selection
        
        # Debugging: Print received values
        print(f'action: {action}')
        print(f'action1: {action1}')
        print(f'selected_transaction_ids: {selected_transaction_ids}')
        print(f'selected_transaction_id: {selected_transaction_id}')
        
        # Handle actions based on POST data
        if action == 'delete':
            if selected_transaction_ids:
                # Mark selected transactions and bookmarks as deleted
                Transactions.objects.filter(transaction_id__in=selected_transaction_ids).update(is_deleted=1,deleted_at = timezone.now())
                Bookmarks.objects.filter(
                    item_id__in=selected_transaction_ids,
                    item_type='Transaction',
                    user_id=request.user.id
                ).update(is_deleted=1)

                # Compute the total price of the selected transactions
                total_price = Transactions.objects.filter(
                    transaction_id__in=selected_transaction_ids,
                    is_deleted=1
                ).aggregate(total_price=Sum('total_transaction_price'))['total_price'] or 0

                # Update project attributes
                project.estimated_budget += total_price
                project.actual_expenditure -= total_price
                project.balance = project.estimated_budget - project.actual_expenditure
                project.save()
                messages.success(request, '')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)

        elif action == 'bookmark':
            if selected_transaction_ids:
                for transaction_id in selected_transaction_ids:
                    try:
                        item_id = int(transaction_id)
                        bookmarkT = Bookmarks(
                            item_type='Transaction',
                            item_id=item_id,
                            user_id=request.user.id,
                            project_id=project.project_id,
                            timestamp=timezone.now(),
                            is_deleted=0
                        )
                        bookmarkT.save()
                        messages.success(request, '')
                    except ValueError:
                        messages.error(request, f'')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)
        
        elif action == 'unbookmark':
            if selected_transaction_ids:
                Bookmarks.objects.filter(
                    item_id__in=selected_transaction_ids,
                    item_type='Transaction',
                    user_id=request.user.id
                ).update(is_deleted=1)
                messages.success(request, '')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)

        elif action1 == 'bookmark1':
            if selected_transaction_id:
                try:
                    item_id = int(selected_transaction_id)
                    bookmarkT = Bookmarks(
                        item_type='Transaction',
                        item_id=item_id,
                        user_id=request.user.id,
                        project_id=project.project_id,
                        timestamp=timezone.now(),
                        is_deleted=0
                    )
                    bookmarkT.save()
                    messages.success(request, '')
                except ValueError:
                    messages.error(request, '')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)

        elif action1 == 'unbookmark1':
            if selected_transaction_id:
                try:
                    item_id = int(selected_transaction_id)
                    Bookmarks.objects.filter(
                        item_id=item_id,
                        item_type='Transaction',
                        user_id=request.user.id
                    ).update(is_deleted=1)
                    messages.success(request, '')
                except ValueError:
                    messages.error(request, '')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)

        elif action1 == 'delete1':
            if selected_transaction_ids:
                Transactions.objects.filter(transaction_id__in=selected_transaction_ids).update(is_deleted=2)
                messages.success(request, '')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)
        
        elif action == 'restore':
            if selected_transaction_ids:
                Transactions.objects.filter(transaction_id__in=selected_transaction_ids).update(is_deleted=0)
                messages.success(request, '')
            else:
                messages.error(request, '')
            return redirect('transactions', pk=pk)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        all_transactions = all_transactions.filter(Q(transaction_name__icontains=search_query)|Q(transaction_details__icontains=search_query))
        total_price_sum = all_transactions.aggregate(total=Sum('total_transaction_price'))['total']

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
    if filter_type == 'internal':
        transactions = all_transactions.filter(transaction_category='Internal')
        total_price_sum = transactions.aggregate(total=Sum('total_transaction_price'))['total']
    elif filter_type == 'external':
        transactions = all_transactions.filter(transaction_category='External')
        total_price_sum = transactions.aggregate(total=Sum('total_transaction_price'))['total']
    elif filter_type == 'bookmarked':
        transactions = bookmarked_transactions
        total_price_sum = transactions.aggregate(total=Sum('total_transaction_price'))['total']
    else:
        transactions = all_transactions
        total_price_sum = transactions.aggregate(total=Sum('total_transaction_price'))['total']

    # Implement pagination (4 transactions per page)
    paginator = Paginator(all_transactions, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        all_transactions = paginator.page(page_number)
    except (ValueError, EmptyPage):
        resources = paginator.page(1)

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

    now = timezone.now() 

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'user_id': request.user.id,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'now': localtime(now),
        'type': profile.user_type,
        'transactions': transactions,
        'leader_profile': leader_profile,
        'project_members': project_member_details,
        'transactions_count': transactions_count,
        'all_transactions': all_transactions,
        'trash_transactions': trash_transactions,
        'internal_count': internal_count,
        'external_count': external_count,
        'trash_transactions_count': trash_transactions_count,
        'bookmark_transactions_count': bookmark_transactions_count,
        'bookmarked_transactions_ids': bookmarked_transactions_ids,
        'transactions_count': transactions_count,
        'status_filter_display': status_filter_display,
        'date_filter_display': date_filter_display,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'total_price_sum': total_price_sum,
        # 'user_votes': user_votes_dict,
        'unread_count': unread_count,
    }
    return render(request, 'transactions.html', context)

@login_required
def edit_message(request, pk):
    if request.method == 'POST':
        message_id = request.POST.get('mid')
        new_message = request.POST.get('edited_message')
        chat = get_object_or_404(Chat, chat_id=message_id, sender_user=request.user)
        chat.message = new_message
        chat.updated_at = timezone.now()
        chat.save()
        return redirect('chat', pk=pk)
    return redirect('chat', pk=pk)

@login_required
def gantt(request, pk):
    user = request.user
    project = pk
    profile = user.profile
    user_id = profile.user_id
    now = timezone.now()
    today = now.date()  # Current date
    current_time = now.time()  # Current time

    print(f'today: {today}')
    print(f'current time: {current_time}')

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
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

    date_filter_display = ""
    filter_type = ""

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
            task_status='Ongoing'
        )
        pending_tasks_counts = all_pending_tasks.count()

    # Get project and related information
    project = get_object_or_404(Projects, pk=pk)

    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)
    project_member_details = []
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'user_type': member_profile.user_type,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)

    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Event', project_id=project.project_id, user_id=request.user.id)
    bookmarked_events_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_events = Events.objects.filter(event_id__in=bookmarked_events_ids)
    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()               

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
            'user_type': member_profile.user_type,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)
    
    # Assuming `task.task_given_date` and `task.task_due_date` are date objects
    current_date = datetime.now().date()
    
    now = timezone.now()

    # Prepare the context
    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'now': localtime(now),
        'project': project,
        'type': profile.user_type,
        'leader_profile': leader_profile,
        'project_members': project_member_details,
        'today': today,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'unread_count': unread_count,     
    }

    return render(request, 'gantt.html', context)

@login_required
def tasks(request, pk):
    user = request.user
    project = pk
    profile = user.profile
    user_id = profile.user_id
    now = timezone.now()
    today = now.date()  # Current date
    current_time = now.time()  # Current time

    print(f'today: {today}')
    print(f'current time: {current_time}')

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
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
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
            task_status='Ongoing'
        )
        pending_tasks_counts = all_pending_tasks.count()

    # Get project and related information
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # Fetch tasks
    # Get all tasks related to the project
    tasks = Tasks.objects.filter(project_id=pk, is_deleted=0).distinct()

    # Get ongoing tasks assigned to the current user
    ptasks = Tasks.objects.filter(
        project_id=pk,
        member__in=[request.user],  # Filter for tasks where the current user is one of the members
        is_deleted=0,
        task_status='Ongoing'
    ).distinct()

    pending_tasks = ptasks.count()

    # Get completed tasks assigned to the current user
    # ctasks = Tasks.objects.filter(project_id=pk, member__in=[request.user], is_deleted=0).values('task_status')

    ctasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    ).distinct()

    completed_tasks = ctasks.count()

    # Get overdue tasks assigned to the current user
    otasks = Tasks.objects.filter(
        project_id=pk,
        member__in=[request.user],  # Filter for tasks where the current user is one of the members
        is_deleted=0,
        task_days_overdue__gt=0
    ).distinct()

    overdue_tasks = otasks.count()

    # For the entire project, get ongoing tasks (for project leaders/admins)
    p1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_status='Ongoing'
    ).distinct()

    pending_tasks1 = p1tasks.count()

    # For the entire project, get completed tasks (for project leaders/admins)
    c1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    ).distinct()

    completed_tasks1 = c1tasks.count()

    # For the entire project, get overdue tasks (for project leaders/admins)
    o1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_days_overdue__gt=0,
        task_status='Ongoing'
    ).distinct()

    overdue_tasks1 = o1tasks.count()

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)
    project_member_details = []
    for member in project_members:
        member_profile = Profile.objects.get(user_id=member.user_id)
        member_info = {
            'first_name': member_profile.user.first_name,
            'last_name': member_profile.user.last_name,
            'phone_number': member_profile.phone_number,
            'user_type': member_profile.user_type,
            'image': member_profile.profile_picture.url if member_profile.profile_picture else None,
            'id': member_profile.user.id,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)

    members_with_completed_tasks = []

    # Loop through each project member
    for member in project_member_details:
        # Get the completed tasks assigned to this member
        member_task = ctasks.filter(member__id=member['id']) 
        member_task1 = c1tasks.filter(member__id=member['id']) 

        member_tasks = (member_task | member_task1).distinct()        
        # Add the member details and their completed tasks to the list
        members_with_completed_tasks.append({
            'member': member,
            'completed_tasks': member_tasks
        })

    # Implement pagination (4 pending tasks for project owner per page)
    paginator1 = Paginator(p1tasks, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        p1tasks = paginator1.page(page_number)
    except (ValueError, EmptyPage):
        p1tasks = paginator1.page(1)

    # Implement pagination (4 pending tasks for project member per page)
    paginator2 = Paginator(ptasks, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        p1asks = paginator2.page(page_number)
    except (ValueError, EmptyPage):
        ptasks = paginator2.page(1)   

    # Implement pagination (4 completed tasks for project owner per page)
    paginator3 = Paginator(c1tasks, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        c1tasks = paginator3.page(page_number)
    except (ValueError, EmptyPage):
        c1tasks = paginator3.page(1)

    # Implement pagination (4 completed tasks for project member per page)
    paginator3 = Paginator(ctasks, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        ctasks = paginator3.page(page_number)
    except (ValueError, EmptyPage):
        ctasks = paginator3.page(1)                

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
            'user_type': member_profile.user_type,
            'role': 'client' if member_profile.user_type == 'client' else 'contractor'
        }
        project_member_details.append(member_info)
    
    # Assuming `task.task_given_date` and `task.task_due_date` are date objects
    current_date = datetime.now().date()

    # Prepare the data for Gantt chart
    task_data = []

    # for task in tasks:
    #     current_date = datetime.now().date()

    #     resource = ', '.join(f"{member.first_name} ({member.profile.user_type})" for member in task.member.all())

    #     # Ensure `task.task_given_date` and `task.task_due_date` are properly defined
    #     if task.task_given_date and task.task_due_date:
    #         total_duration = (task.task_due_date - task.task_given_date).days
    #         elapsed_time = (current_date - task.task_given_date).days

    #         # Calculate percent complete
    #         if total_duration > 0:
    #             percent_complete = min(100, (elapsed_time / total_duration) * 100)
    #         else:
    #             percent_complete = 100 if task.task_due_date < current_date else 0
    #     else:
    #         percent_complete = 0

    #     task_data.append({
    #         'task_id': task.task_id,
    #         'task_name': task.task_name,
    #         'resource': resource if resource else '',
    #         'start_date': task.task_given_date.strftime('%Y, %m, %d') if task.task_given_date else None,
    #         'end_date': task.task_due_date.strftime('%Y, %m, %d') if task.task_due_date else None,
    #         'duration': (task.task_due_date - task.task_given_date).days if task.task_given_date and task.task_due_date else 0,
    #         'percent_complete': percent_complete,
    #         'dependencies': ', '.join(str(dep.id) for dep in task.dependant_tasks.all()) if task.dependant_tasks.exists() else ''
    #     })

    # # Convert task_data to JSON
    # task_data_json = json.dumps(task_data)

    # for task in tasks:
    #     for member in task.member.all():  # Assuming `member` is a ManyToManyField
    #         task_data.append([
    #             str(task.task_id),  # Task ID
    #             task.task_name,  # Task Name
    #             f"{member.first_name} ({member.profile.user_type})",  # Resource
    #             task.task_given_date.strftime('%Y, %m, %d'),  # Start Date
    #             task.task_due_date.strftime('%Y, %m, %d'),  # End Date
    #             (task.task_due_date - task.task_given_date).days,  # Duration
    #             task.task_percentage_complete,  # Percent Complete
    #             ', '.join(str(dep.id) for dep in task.dependant_tasks.all())  # Dependencies
    #         ])
    
    # task_data_json = json.dumps(task_data)
    # return JsonResponse({'tasks': task_data})
    
    now = timezone.now()

    # Prepare the context
    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'now': localtime(now),
        'project': project,
        'type': profile.user_type,
        'tasks': tasks,
        'ptasks': ptasks,
        'ctasks': ctasks,
        'p1tasks': p1tasks,
        'c1tasks': c1tasks,
        'otasks': otasks,
        'o1tasks': o1tasks,
        'events': events,
        'completed_tasks': completed_tasks,
        'pending_tasks1': pending_tasks1,
        'completed_tasks1': completed_tasks1,
        'overdue_tasks1': overdue_tasks1,
        'overdue_tasks': overdue_tasks,
        'leader_profile': leader_profile,
        'pending_tasks': pending_tasks,
        'project_members': project_member_details,
        'today': today,
        'pending_tasks': pending_tasks,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        # 'task_data_json': task_data_json,
        'members_with_completed_tasks': members_with_completed_tasks,
        'task_data': task_data,  
        'unread_count': unread_count,      
    }

    return render(request, 'tasks.html', context)

@login_required
def update_task(request, task_id):
    task = get_object_or_404(Tasks, task_id=task_id, is_deleted=0)

    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task_details = request.POST.get('task_details')
        task_due_date = request.POST.get('task_due_date')

        # Update the task details
        if task_name and task_details and task_due_date:
            task.task_name = task_name
            task.task_details = task_details
            task.task_due_date = task_due_date
            task.save()
            messages.success(request, 'Task updated successfully.')
        else:
            messages.error(request, 'Please fill in all fields.')

    return redirect('tasks', pk=task.project_id)  # Redirect back to the tasks list

@login_required
def dashboard(request, pk):
    user = request.user
    profile = user.profile
    now = date.today() 
    now = timezone.now()       
    today = now.date()  # Current date
    current_time = now.time()  # Current time
    project = get_object_or_404(Projects, pk=pk)
    project_id = project.project_id

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    unread_chat_counts = {}
    pending_tasks_counts = {}
    all_tasks_counts = {}

    all_unread_chats = []
    all_pending_tasks = []
    all_tasks = []

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project1,
            is_deleted=0,
            task_status='Ongoing',
        )
        pending_tasks_counts = all_pending_tasks.count()

    # Total Tasks
    total_tasks = Tasks.objects.filter(project_id=project_id, is_deleted=0).count()

    # Get current date and compute month and last month for expense calculations
    now1 = datetime.now()
    current_month = now1.strftime('%Y-%m')
    last_month = (now1 - timedelta(days=30)).strftime('%Y-%m')

    # Expenses
    month_to_date_expenses = Transactions.objects.filter(
        project_id=project_id,
        created_at__year=now.year,
        created_at__month=now.month,
        is_deleted=0
    ).aggregate(total_expenses=Sum('total_transaction_price'))['total_expenses'] or 0

    last_month_expenses = Transactions.objects.filter(
        project_id=project_id,
        created_at__year=now.year,
        created_at__month=(now.month - 1 if now.month > 1 else 12),
        is_deleted=0
    ).aggregate(total_expenses=Sum('total_transaction_price'))['total_expenses'] or 0

    remaining_budget = project.balance

    # Month to Date Expenses Data
    month_to_date_data = [
        last_month_expenses,
        month_to_date_expenses,
        #month_to_date_expenses * 1.1  # Example forecast
        remaining_budget,
    ]

    # Get the date range from the request, or set default values
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # If no date range is provided, set default to the current month
    if not start_date or not end_date:
        now = datetime.now()
        start_date = now.strftime('%Y-%m-01')  # Start of current month
        end_date = now.strftime('%Y-%m-30')  # Today

    # Filter Tasks, Transactions, and Events based on the selected date range

    # Ontime Task Completion Rate
    completed_tasks = Tasks.objects.filter(
        project_id=project_id,
        task_status__in=['Completed Early','Completed Today'],
        task_completed_date__lte=F('task_due_date'),
        task_given_date__range=[start_date, end_date]  # Filter by date range
    ).count()

    total_due_tasks = Tasks.objects.filter(
        project_id=project_id,
        is_deleted=0,
        task_given_date__range=[start_date, end_date]  # Filter by date range
    ).count()

    ontime_task_completion_rate = (completed_tasks / total_due_tasks * 100) if total_due_tasks else 0

    # Work Load Per Member
    # work_load_data = Tasks.objects.filter(
    #     project_id=project_id,
    #     is_deleted=0,
    #     task_given_date__range=[start_date, end_date]  # Filter by date range
    # ).annotate(
    #     full_name=Concat(F('member__first_name'), Value(' '), F('member.profile.user_type'))
    # ).values('full_name').annotate(
    #     task_count=Count('task_id')
    # ).order_by('-task_count')

    # work_load_labels = [f'{item["full_name"]}' for item in work_load_data]
    # work_load_data_values = [item['task_count'] for item in work_load_data]

    # Get tasks based on project ID and date range
    tasks = Tasks.objects.filter(
        project_id=project_id,
        is_deleted=0,
        task_given_date__range=[start_date, end_date]
    )

    # Annotate each task with the associated member's full name and user type
    # Note: You should use `prefetch_related` to reduce the number of database queries if you have a lot of members
    tasks = tasks.prefetch_related('member')

    # Create a dictionary to count tasks per member
    work_load = {}
    for task in tasks:
        for member in task.member.all():
            # Generate a unique identifier for the member using full name and user type
            member_id = f'{member.first_name} ({member.profile.user_type})'
            if member_id in work_load:
                work_load[member_id] += 1
            else:
                work_load[member_id] = 1

    # Convert the dictionary to lists for chart.js
    work_load_labels = list(work_load.keys())
    work_load_data_values = list(work_load.values())

    # Types of Transactions
    transaction_data = Transactions.objects.filter(
        project_id=project_id,
        is_deleted=0,
        created_at__range=[start_date, end_date]  # Filter by date range
    ).values('transaction_category').annotate(
        sum=Sum('total_transaction_price')
    ).order_by('-sum')

    transaction_labels = [item['transaction_category'] for item in transaction_data]
    transaction_data_values = [item['sum'] for item in transaction_data]

    # Events Timeline
    events_data = Events.objects.filter(
        project_id=project_id,
        is_deleted=0,
        event_date__range=[start_date, end_date]  # Filter by date range
    ).values('event_date').annotate(
        event_count=Count('event_id')
    ).order_by('event_date')

    events_labels = [item['event_date'].strftime('%Y-%m-%d') for item in events_data]
    events_data = [item['event_count'] for item in events_data]

    # Task Status Data
    task_status_data = Tasks.objects.filter(
        project_id=project_id,
        is_deleted=0,
        task_given_date__range=[start_date, end_date]  # Filter by date range
    ).values('task_status').annotate(
        status_count=Count('task_id')
    ).order_by('task_status')

    task_status_labels = [item['task_status'] for item in task_status_data]
    task_status_data_values = [item['status_count'] for item in task_status_data]

    members_users_count = ProjectMembers.objects.filter(
        project_id=project_id,
        is_deleted=0, 
        status='Accepted'
    ).count()

    total_users_count = 1 + members_users_count 

    online_users_subquery = Users.objects.filter(
        is_deleted=0,
        online=1
    ).values('user_id')

    # Get the number of online users associated with the current project
    online_users_count = ProjectMembers.objects.filter(
        project_id=project_id,
        is_deleted=0,
        status='Accepted',        
        user__in=Subquery(online_users_subquery)
    ).count()

    # Calculate the average percentage of online users
    average_online_percentage = (online_users_count / total_users_count * 100) if total_users_count else 0

    # Prepare data for the chart
    # Assuming you'll need labels and data for the chart
    online_labels = ['Online Users', 'Total Users']
    online_data_values = [online_users_count + 1, total_users_count]

    # Filter chats for the specific project
    chats = Chat.objects.filter(
        group__project_id=project_id,
        is_deleted=0,
        chatstatus__status=1 
    )

    # Get unread message counts per user
    unread_counts = chats.values('chatstatus__user_id').annotate(
        unread_messages=Count('chat_id'),
        user_first_name=Subquery(
            User.objects.filter(id=OuterRef('chatstatus__user_id')).values('first_name')[:1]
        ),
        user_type=Subquery(
            Profile.objects.filter(user_id=OuterRef('chatstatus__user_id')).values('user_type')[:1]
        )
    ).order_by('-unread_messages')

    # Prepare data for the chart
    unread_labels = [f'{item["user_first_name"]} ({item["user_type"]})' for item in unread_counts]  # Adjusted as sender_user__id is used
    unread_data_values = [item['unread_messages'] for item in unread_counts]

    context = {
        'total_tasks': total_tasks,
        'month_to_date_expenses': month_to_date_expenses,
        'last_month_expenses': last_month_expenses,
        'ontime_task_completion_rate': ontime_task_completion_rate,
        'work_load_labels': work_load_labels,
        'work_load_data_values': work_load_data_values,
        'transaction_labels': transaction_labels,
        'transaction_data_values': transaction_data_values,
        'events_labels': events_labels,
        'events_data': events_data,
        'month_to_date_data': month_to_date_data,
        'task_status_labels': task_status_labels,
        'task_status_data_values': task_status_data_values,
        'online_labels': online_labels,
        'online_data_values': online_data_values,
        'unread_labels': unread_labels,
        'unread_data_values': unread_data_values,
        # 'total_tasks': 150,
        # 'month_to_date_expenses': 5000.00,
        # 'last_month_expenses': 4500.00,
        # 'ontime_task_completion_rate': 85.5,
        # 'work_load_labels': ['Member A', 'Member B', 'Member C'],
        # 'work_load_data': [20, 35, 25],
        # 'transaction_labels': ['Type 1', 'Type 2', 'Type 3'],
        # 'transaction_data': [30, 40, 30],
        # 'events_labels': ['Jan', 'Feb', 'Mar'],
        # 'events_data': [10, 15, 20],
        # 'month_to_date_data': [1000, 2000, 1500],
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture if profile.profile_picture else None,
        'type': profile.user_type,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'project_id': project_id,
        'now': now,
        'pending_tasks_counts': pending_tasks_counts,
        'unread_count': unread_count,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        }

    return render(request, 'project-dashboard.html', context)

@login_required
def events(request, pk):
    user = request.user
    profile = user.profile
    user_id = profile.user_id
    now = timezone.now()
    today = now.date()  # Current date
    current_time = now.time()  # Current time

    print(f'today: {today}')
    print(f'current time: {current_time}')

    # Get project and related information
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)
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

    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Event', project_id=project.project_id, user_id=request.user.id)
    bookmarked_events_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_events = Events.objects.filter(event_id__in=bookmarked_events_ids)
    bookmarked_events_count = bookmarked_events.count()
    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
    trash_events = Events.objects.filter(project_id=pk, is_deleted=1)
    trash_events_count = trash_events.count()

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
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

    date_filter_display = ""
    filter_type = ""

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
            task_status='Ongoing'
        )
        pending_tasks_counts = all_pending_tasks.count()
        # Filter events that have passed or not passed

    # Active (Upcoming) Events: event_date >= today OR event_end_time > current_time
    aevents = Events.objects.filter(
        project_id=pk,
        is_deleted=0,
        event_status='Scheduled',
    )

    a1events = aevents.count()

    # Complete (Passed) Events: event_date < today AND event_end_time <= current_time
    cevents = Events.objects.filter(
        project_id=pk,
        event_status='Completed',
        is_deleted=0
    )

    c1events = cevents.count()

    ecounts = (aevents | bookmarked_events | cevents).distinct().count()

    events = (cevents | aevents | bookmarked_events).distinct()

    if request.method == "POST":
        action = request.POST.get('action')
        action1 = request.POST.get('action1')
        selected_event_ids = request.POST.getlist('selected_events')  # Handles multiple selections
        selected_event_id = request.POST.get('selected_event')  # Handles single selection
        
        # Debugging: Print received values
        print(f'action: {action}')
        print(f'action1: {action1}')
        print(f'selected_event_ids: {selected_event_ids}')
        print(f'selected_event_id: {selected_event_id}')

        if action == 'bookmark':
            if selected_event_ids:
                for event_id in selected_event_ids:
                    try:
                        item_id = int(event_id)
                        bookmarkE = Bookmarks(
                            item_type='Event',
                            item_id=item_id,
                            user_id=request.user.id,
                            project_id=project.project_id,
                            timestamp=timezone.now(),
                            is_deleted=0
                        )
                        bookmarkE.save()
                        messages.success(request,'')
                    except ValueError:
                        messages.error(request, f'Invalid events ID: {resource_id}.')
            else:
                messages.error(request, '')
        
        elif action == 'unbookmark':
            if selected_event_ids:
                Bookmarks.objects.filter(
                    item_id__in=selected_event_ids,
                    item_type='Event',
                    user_id=request.user.id
                ).update(is_deleted=1)
                messages.success(request, '')
            else:
                messages.error(request, '')

        elif action1 == 'bookmark1':
            if selected_event_id:
                try:
                    item_id = int(selected_event_id)
                    bookmarkE = Bookmarks(
                        item_type='Event',
                        item_id=item_id,
                        user_id=request.user.id,
                        project_id=project.project_id,
                        timestamp=timezone.now(),
                        is_deleted=0
                    )
                    bookmarkE.save()
                    messages.success(request, '')
                except ValueError:
                    messages.error(request, '')
            else:
                messages.error(request, '')

        elif action1 == 'unbookmark1':
            if selected_event_id:
                try:
                    item_id = int(selected_event_id)
                    Bookmarks.objects.filter(
                        item_id=item_id,
                        item_type='Event',
                        user_id=request.user.id
                    ).update(is_deleted=1)
                    messages.success(request, '')
                except ValueError:
                    messages.error(request, '')
            else:
                messages.error(request, '')

        elif action1 == 'delete1':
            if selected_event_ids:
                Events.objects.filter(event_id__in=selected_event_ids).update(is_deleted=2)
                messages.success(request, '')
            else:
                messages.error(request, '')

        elif action == 'delete':
            if selected_event_ids:
                Events.objects.filter(event_id__in=selected_event_ids).update(is_deleted=1,deleted_at = timezone.now())
                Bookmarks.objects.filter(
                    item_id__in=selected_event_ids,
                    item_type='Event',
                    user_id=request.user.id
                ).update(is_deleted=1)
            else:
                messages.error(request, '')

        action = None
        action1 = None
        selected_event_ids = []
        selected_event_id = []

        return redirect('events', pk=pk)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        events = events.filter(Q(event_name__icontains=search_query)|Q(event_details__icontains=search_query))

    # Apply date filtering
    date_filter = request.GET.get('date_filter')
    if date_filter:
        if date_filter == 'today':
            events = events.filter(created_at__date=current_date)
            date_filter_display = "Today"
        elif date_filter == 'this_week':
            start_of_week = current_date - timedelta(days=current_date.weekday())
            events = events.filter(created_at__date__gte=start_of_week)
            date_filter_display = "This Week"
        elif date_filter == 'this_month':
            events = events.filter(created_at__year=current_date.year, created_at__month=current_date.month)
            date_filter_display = "This Month"
        elif date_filter == 'this_year':
            events = events.filter(created_at__year=current_date.year)
            date_filter_display = "This Year"

    # Get the filter type from the query parameters (default to 'all')
    filter_type = request.GET.get('filter', 'all')

    # Apply filtering based on the selected filter type
    if filter_type == 'completed':
        events = cevents
    elif filter_type == 'active':
        events = aevents
    elif filter_type == 'bookmarked':
        events = bookmarked_events
    else:
        events = events

    # Implement pagination (4 events per page)
    paginator = Paginator(events, 4)
    page_number = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        events = paginator.page(page_number)
    except (ValueError, EmptyPage):
        events = paginator.page(1)                

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

    expired_events = Events.objects.filter(
        event_date__lte=today,
        event_end_time__lte=now.time(),
        is_deleted=0
    ) 

    for event in expired_events:
        if event.event_status != 'Completed':
            event.event_status = 'Completed'
            event.save()
    
    # Prepare the context
    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'now': localtime(now),
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'project': project,
        'c1events': c1events,
        'a1events': a1events,        
        'type': profile.user_type,
        'user_id': user_id,
        'events': events,
        'ecounts': ecounts, 
        'leader_profile': leader_profile,
        'project_members': project_member_details,
        'today': today,
        'bookmarked_events_ids': bookmarked_events_ids,
        'trash_events': trash_events,
        'trash_events_count': trash_events_count,
        'bookmarked_events_count': bookmarked_events_count,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'date_filter_display': date_filter_display,
        'filter_type': filter_type,
        'unread_count': unread_count,
    }

    return render(request, 'events.html', context)


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
        
        messages.success(request, '')
        return redirect('events', pk=pk)  # Assuming you have a 'project_events' view
    
    # If not POST, redirect to the project events page
    return redirect('events', pk=pk)

@login_required
def delete_event(request, pk, event_id):
    event = get_object_or_404(Events, pk=event_id, project__pk=pk)
    event.is_deleted = 1
    event.deleted_at = timezone.now()
    event.save()
    Bookmarks.objects.filter(
        item_id=event_id,
        item_type='Event',
        user_id=request.user.id
    ).update(is_deleted=1)
    return redirect('events', pk=pk)

@login_required
def add_task(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Projects, pk=pk)
        
        # Get the list of member IDs from the form
        member_ids = request.POST.getlist('members[]')
        
        # Get the list of users based on these IDs
        members = User.objects.filter(id__in=member_ids)

        # Parse dates
        task_given_date = timezone.now().date()
        task_due_date = datetime.strptime(request.POST['due_date'], '%Y-%m-%d').date()

        # Calculate days left
        days_left = (task_due_date - task_given_date).days

        # Create a new task
        task = Tasks(
            leader=request.user,  # Assuming the current user is the leader
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
        
        # Add members to the task
        task.member.set(members)  # Use the set() method to assign multiple members

        messages.success(request, '')
        return redirect('tasks', pk=pk)  # Assuming you have a 'project_tasks' view
    
    # If not POST, redirect to the project tasks page
    return redirect('tasks', pk=pk)


@login_required
def delete_task(request, pk, task_id):
    task = get_object_or_404(Tasks, pk=task_id, project__pk=pk).delete()
    return redirect('tasks', pk=pk)

@login_required
def complete_task(request, pk, task_id):
    task = get_object_or_404(Tasks, pk=task_id, project__pk=pk)
    task.task_status = 'Completed Today'
    if task.days_to_complete > 0:
        task.task_status = 'Completed Early'   
    elif task.days_to_complete == 0:
        task.task_status = 'Completed Today'
    else:
        task.task_status = f'Completed Late (by {task.days_overdue} days)'     
    task.task_completed_date = timezone.now()
    task.save()
    return redirect('tasks', pk=pk)

@login_required
def delete_project(request, pk):
    project = get_object_or_404(Projects, project_id=pk)

    # Check if the logged-in user is the project leader
    if project.project_leader != request.user:
        messages.error(request, "You do not have permission to delete this project.")
        return redirect('client')

    # Proceed with deletion if the user is the project leader
    project.is_deleted = 1
    project.deleted_at = timezone.now()
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
def restore_event(request, pk, event_id):
    events = get_object_or_404(Events, event_id=event_id, project_id=pk)
    events.is_deleted = 0
    events.save()
    return redirect('events', pk=pk)

@login_required
def hide_event(request, pk, event_id):
    get_object_or_404(Events, pk=event_id, project__pk=pk).delete()
    return redirect('events', pk=pk)

@login_required
def restore_task(request, pk, task_id):
    events = get_object_or_404(Events, task_id=task_id, project_id=pk)
    events.is_deleted = 0
    events.save()
    return redirect('tasks', pk=pk)

@login_required
def hide_task(request, pk, task_id):
    get_object_or_404(Tasks, pk=task_id, project__pk=pk).delete()
    return redirect('tasks', pk=pk)    

@login_required
def chat(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    user_id = profile.user_id
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    leader_user = Users.objects.get(user_id=project.leader_id)

    # Update chat status from 1 to 0 for the logged-in user
    ChatStatus.objects.filter(user_id=user.id, group=project.groupchat, status=1).update(status=0)

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)

    # Retrieve user details for project members
    project_member_details = []
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
            'user_type': member_profile.user_type,
            'logged_in': member_user.logged_in,
            'logged_out': member_user.logged_out, 
        }
        project_member_details.append(member_info)

    # Fetch chat messages for the current project
    messages = Chat.objects.filter(group=project.groupchat, is_deleted=0).order_by('timestamp')
    pinned_messages = Chat.objects.filter(group_id=project.groupchat, is_pinned=1, is_deleted=0).order_by('timestamp')


    bookmarks = Bookmarks.objects.filter(is_deleted=0, item_type='Chat', user_id=request.user.id)
    bookmarked_chat_ids = bookmarks.values_list('item_id', flat=True)
    bookmarked_chats = Chat.objects.filter(chat_id__in=bookmarked_chat_ids)
    chat_messages = (messages | bookmarked_chats).distinct()

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
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
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
            task_status='Ongoing'
        )
        pending_tasks_counts = all_pending_tasks.count()

    search_query = request.GET.get('search', '').strip()
    if search_query:
        chat_messages = chat_messages.filter(message__icontains=search_query)

    # Apply status filtering
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'bookmarked':
        chat_messages = bookmarked_chats
        status_filter_display = "Bookmarked Chats"
    else:
        chat_messages = chat_messages
        status_filter_display = "All Projects"

    # Group messages by date
    grouped_messages = {}
    for message in chat_messages:
        date_str = message.timestamp.strftime("%d %b %Y")
        if date_str not in grouped_messages:
            grouped_messages[date_str] = []
        grouped_messages[date_str].append(message)

    now = timezone.now() 

    # Update chat status from 1 to 0 for the logged-in user
    ChatStatus.objects.filter(user_id=user.id, group=project.groupchat, status=1).update(status=0)

    for message in chat_messages:
        if message.file:
            message.file_extension = os.path.splitext(message.file)[1].lower().strip('.')
        else:
            message.file_extension = ''

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image1': profile.profile_picture.url if profile.profile_picture else None,
        'type': profile.user_type,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'user_id': profile.user_id,
        'project': project,
        'now': localtime(now),
        'leader_profile': leader_profile,
        'member_status': member.status,
        'project_member_details': project_member_details,
        'chat_messages': chat_messages,  
        'pinned_messages': pinned_messages,
        'grouped_messages': grouped_messages,
        'bookmarked_chat_ids': bookmarked_chat_ids,
        'now': localtime(now),
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'unread_count': unread_count,
    }
    return render(request, 'chat.html', context)

@login_required
def pin_message(request, project_id):
    if request.method == "POST":
        chat_id = request.POST.get('chat_id')
        message = get_object_or_404(Chat, chat_id=chat_id)
        message.is_pinned = 1
        message.save()
    return redirect('chat', pk=project_id)

@login_required
def unpin_message(request, project_id):
    if request.method == "POST":
        chat_id = request.POST.get('chat_id')
        message = get_object_or_404(Chat, chat_id=chat_id)
        message.is_pinned = 0
        message.save()
    return redirect('chat', pk=project_id)

@login_required
def bookmark_message(request, project_id):
    if request.method == "POST":
        chat_id = request.POST.get('chat_id')
        bookmarkC = Bookmarks(
            item_type='Chat',
            item_id=chat_id,
            user_id=request.user.id,
            project_id=project_id,
            timestamp=timezone.now(),
            is_deleted=0
            )
        bookmarkC.save()
    return redirect('chat', pk=project_id)

@login_required
def unbookmark_message(request, project_id):
    if request.method == "POST":
        chat_id = request.POST.get('chat_id')
        Bookmarks.objects.filter(
            item_id=chat_id,
            item_type='Chat',
            user_id=request.user.id
            ).update(is_deleted=1)
    return redirect('chat', pk=project_id)

@login_required
def project_detail(request, pk):
    user = request.user
    profile = user.profile
    now = date.today()
    type = profile.user_type
    user_id = profile.user_id
    today = now.strftime('%Y-%m-%d')
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)
    leader_user = Users.objects.get(user_id=project.leader_id)

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    unread_chat_counts = {}
    pending_tasks_counts = {}
    pending_tasks_counts1 = {}
    all_tasks_counts = {}
    progress_percentages = {}
    total_progress_percentages = {}

    all_unread_chats = []
    all_pending_tasks = []
    all_tasks = []

    # Calculate unread chat statuses and pending tasks for each project
    for project1 in projects:
        try:
            group_chat = GroupChat.objects.get(project=project1)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_count = all_unread_chats.count()
        except GroupChat.DoesNotExist:
            unread_count = 0

        # Count pending tasks
        all_pending_tasks = Tasks.objects.filter(
            project=project1,
            is_deleted=0,
            task_status='Ongoing',
        )
        pending_tasks_counts = all_pending_tasks.count()

    # Query for project members
    project_members = ProjectMembers.objects.filter(project=project, is_deleted=0)
    project_member_ids = project_members.values_list('user_id', flat=True)

    project_membersC = project_members.count()

    # Get all tasks related to the project
    tasks = Tasks.objects.filter(project_id=pk, is_deleted=0).distinct()

    # Get ongoing tasks assigned to the current user
    ptasks = Tasks.objects.filter(
        project_id=pk,
        member__in=[request.user],  # Filter for tasks where the current user is one of the members
        is_deleted=0,
        task_status='Ongoing'
    ).distinct()

    pending_tasks = ptasks.count()

    # Get completed tasks assigned to the current user
    ctasks = Tasks.objects.filter(
        project_id=pk,
        member__in=[request.user],  # Filter for tasks where the current user is one of the members
        is_deleted=0,
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    ).distinct()

    completed_tasks = ctasks.count()

    # Get overdue tasks assigned to the current user
    otasks = Tasks.objects.filter(
        project_id=pk,
        member__in=[request.user],  # Filter for tasks where the current user is one of the members
        is_deleted=0,
        task_days_overdue__gt=0
    ).distinct()

    overdue_tasks = otasks.count()

    # For the entire project, get ongoing tasks (for project leaders/admins)
    p1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_status='Ongoing'
    ).distinct()

    pending_tasks1 = p1tasks.count()

    # For the entire project, get completed tasks (for project leaders/admins)
    c1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_status__in=['Completed Early', 'Completed Today', 'Completed Late']
    ).distinct()

    completed_tasks1 = c1tasks.count()

    # For the entire project, get overdue tasks (for project leaders/admins)
    o1tasks = Tasks.objects.filter(
        project_id=pk,
        is_deleted=0,
        task_days_overdue__gt=0,
        task_status='Ongoing'
    ).distinct()

    overdue_tasks1 = o1tasks.count()

    # Calculate the progress percentage for the project
    if project.end_date and project.start_date:
        total_project_days = (project.end_date - project.start_date).days
        days_passed = (now - project.start_date).days
        if total_project_days > 0:
            progress_percentage = (days_passed / total_project_days) * 100
            if progress_percentage > 0: 
                progress_percentage = progress_percentage  
            else:
                progress_percentage = 0   
        else:
            progress_percentage = 0
    else:
        progress_percentage = 0

    all_pending_tasks1 = Tasks.objects.filter(
        project=project,
        is_deleted=0,
    ).exclude(
        task_status='Ongoing',
    )
    pending_tasks_counts1 = all_pending_tasks1.count()

    # Count pending tasks
    all_tasks = Tasks.objects.filter(
        project=project,
        is_deleted=0,
    )
    all_tasks_counts = all_tasks.count()  

    if pending_tasks1 == 0:
        total_progress_percentage = 100
    elif all_tasks_counts > 0:
        total_progress_percentage = (
            pending_tasks_counts1 / all_tasks_counts
        ) * 100
    else:
        total_progress_percentage = 0

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
            'user_type': member_profile.user_type,
            'logged_in': member_user.logged_in,
            'logged_out': member_user.logged_out,            
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
        user_details = paginator.page(1)

    # Fetch unread messages from ChatStatus table
    unread_messages = ChatStatus.objects.filter(user_id=user.id, group=project.groupchat, status=1, is_deleted=0)

    project_tasks = Tasks.objects.filter(project=project, is_deleted=0)

    events = Events.objects.filter(project_id=pk, user=user.id, is_deleted=0)
    pending_tasks = ptasks.count()
    completed_tasks = ctasks.count()
    pending_tasks1 = p1tasks.count()
    completed_tasks1 = c1tasks.count()

    paginator1 = Paginator(p1tasks, 2)
    page_number1 = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number1 = int(page_number1)
        if page_number1 < 1:
            page_number1 = 1
        p1tasks = paginator1.page(page_number1)
    except (ValueError, EmptyPage):
        p1tasks = paginator1.page(1)

    paginator2 = Paginator(ptasks, 2)
    page_number2 = request.GET.get('page', 1)  # Default to page 1 if not provided
    try:
        page_number2 = int(page_number2)
        if page_number2 < 1:
            page_number2 = 1
        ptasks = paginator1.page(page_number2)
    except (ValueError, EmptyPage):
        ptasks = paginator1.page(1)

    now = timezone.now() 

    context = {
        'auth_user': request.user,
        'fname': user.first_name,
        'image': profile.profile_picture if profile.profile_picture else None,
        'type': profile.user_type,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'now': now,
        'now': localtime(now),
        'project': project,
        'leader_profile': leader_profile,
        'member_status': member_status,
        'user_details': user_details,
        'project_member_details': project_member_details,
        'unread_messages': unread_messages,
        'ptasks': ptasks,
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
        'pending_tasks_counts': pending_tasks_counts,
        'project_membersC': project_membersC,
        'progress_percentage': progress_percentage,
        'total_progress_percentage': total_progress_percentage,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'type': type,
        'open_pmembers': open_pmembers,
        'overdue_tasks1': overdue_tasks1,
        'overdue_tasks': overdue_tasks,
        'otasks': otasks,
        'o1tasks': o1tasks,
        'unread_count': unread_count,
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
            chat_message.deleted_at = timezone.now()
            chat_message.save()
            

            # Set the is_deleted flag to 1 for related ChatStatus entries
            chat_statuses = ChatStatus.objects.filter(chat=chat_message)
            for chat_status in chat_statuses:
                chat_status.is_deleted = 1
                chat_status.deleted_at = timezone.now()
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
def reply_message(request, pk):
    user = request.user
    project = get_object_or_404(Projects, pk=pk)

    if request.method == 'POST':
        reply_message = request.POST.get('reply_message')
        reply_message_id = request.POST.get('reply_message_id')

        original_message = get_object_or_404(Chat, chat_id=reply_message_id)

        new_reply = Chat.objects.create(
            group=project.groupchat,
            sender_user=user,
            message=reply_message,
            reply=original_message.message,  # Set the original message as the reply
            timestamp=timezone.now(),
            is_deleted=0
        )

        return redirect('chat', pk=project.pk)

@login_required
def send_message(request, pk):
    user = request.user
    now = date.today()
    today = now.strftime('%Y-%m-%d')
    profile = user.profile
    project = get_object_or_404(Projects, pk=pk)
    leader_profile = Profile.objects.get(user_id=project.leader_id)

    if request.method == 'POST':
        # Get form data
        message1 = request.POST.get('message')
        uid = request.POST.get('uid')
        file = request.FILES.get('file')
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        reply_message_id = request.POST.get('reply_message_id')

        # Combine scheduled_date and scheduled_time into a single datetime object
        scheduled_at = None
        if scheduled_date and scheduled_time:
            scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")

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

        # If a scheduled time is provided, set the timestamp to that time
        timestamp = scheduled_at if scheduled_at else timezone.now()

        original_message = None
        if reply_message_id:
            # This is a reply to another message
            original_message = get_object_or_404(Chat, chat_id=reply_message_id)

        # Create a new chat message
        new_chat = Chat.objects.create(
            group=project.groupchat,
            sender_user=sender_user,
            message=message,
            timestamp=timestamp,
            is_deleted=0,
            reply=original_message.message if original_message else None,  # Check if original_message exists
            scheduled_at=scheduled_at,
            file=chat_file
        )

        new_chat.save()


        # Implementing the trigger logic
        project_members = ProjectMembers.objects.filter(project=project, is_deleted=0).exclude(user=user)
        logger.info(f"Project members found: {project_members.count()}")

        for project_member in project_members:
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

        if user.id != project.leader_id:
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

    clients_profiles = Profile.objects.filter(user_type='client').exclude(user=user)
    contractors_profiles = Profile.objects.filter(user_type='contractor').exclude(user=user)

    users = list(clients_profiles) + list(contractors_profiles)

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
    user_id = profile.user_id
    today = now.strftime('%Y-%m-%d')

    # Fetch projects where the current user is the leader or a member
    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0, project_status='Active')
    current_date = timezone.now().date()
    # leader_projects.filter(end_date__lt=current_date, project_status__in=['Active']).update(project_status='Completed')
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

    unread_count = 0
    unread_chat_counts = {}
    pending_tasks_counts = {}
    pending_tasks_counts1 = {}
    all_tasks_counts = {}
    progress_percentages = {}
    total_progress_percentages = {}

    all_unread_chats = []
    all_pending_tasks = []
    all_tasks = []

  # Calculate unread chat statuses and pending tasks for each project
    for project in all_projects:
        try:
            group_chat = GroupChat.objects.get(project=project)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_chat_counts[project.project_id] = all_unread_chats1.count()     
            unread_count = all_unread_chats1.count() 
        except GroupChat.DoesNotExist:
            unread_chat_counts[project.project_id] = 0  
            unread_count = 0                    

        all_pending_tasks1 = Tasks.objects.filter(
            project=project,
            is_deleted=0,   
        ).exclude(
            task_status='Ongoing',  
        )
        pending_tasks_counts1[project.project_id] = all_pending_tasks1.count()

        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
            task_status='Ongoing',            
        )
        pending_tasks_counts[project.project_id] = all_pending_tasks.count()

        # Count pending tasks
        all_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
        )
        all_tasks_counts[project.project_id] = all_tasks.count()        

        # Calculate progress value
        total_days = (project.end_date - project.start_date).days
        days_left = (project.end_date - now).days
        progress_percentage = ((total_days - days_left) / total_days) * 100 if total_days > 0 else 0   
        if progress_percentage > 0: 
            progress_percentages[project.project_id] = progress_percentage  
        else:
            progress_percentages[project.project_id] = 0      
        # Calculate progress percentage, handle division by zero
        if all_tasks_counts[project.project_id] > 0:
            total_progress_percentage = (
                pending_tasks_counts1[project.project_id] / all_tasks_counts[project.project_id]
            ) * 100
        elif all_tasks_counts[project.project_id] == 0:
            total_progress_percentage = 0
        elif pending_tasks_counts1[project.project_id] == 0:
            total_progress_percentage = 100            
        else:
            total_progress_percentage = 0

        total_progress_percentages[project.project_id] = total_progress_percentage

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

            projects.update(is_deleted=1, deleted_at=timezone.now())
            Bookmarks.objects.filter(item_id__in=selected_project_ids, item_type='Project', user_id=request.user.id).update(is_deleted=1)
            messages.success(request, '')
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

    now = timezone.now() 

    for project in projects:
        if progress_percentage >= 100 and total_progress_percentage >=100 and project.project_status != 'Completed':
            project.project_status = 'Completed'
            project.save() 
        elif total_progress_percentage < 100 and project.project_status == 'Completed':
            project.project_status = 'Active'
            project.save()   

    context = {
        'fname': user.first_name,
        'user_id': user_id,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'day': today,
        'now': now, 
        'now': localtime(now),
        'projects': projects,
        'filter_type': filter_type,
        'trash_projects': trash_projects,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'progress_percentages': progress_percentages,
        'total_progress_percentages': total_progress_percentages,        
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
        'now': localtime(now),
        'unread_count': unread_count,
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
    today = date.today()
    now = date.today()
    user_type = profile.user_type
    user_id = profile.user_id

    now = timezone.now()

    leader_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=0)
    current_date = timezone.now().date()
    trash_projects = Projects.objects.filter(leader_id=profile.user_id, is_deleted=1)
    member_projects = Projects.objects.filter(
        project_id__in=ProjectMembers.objects.filter(user_id=user.id, is_deleted=0, status='Accepted').values_list('project_id', flat=True),
        is_deleted=0
    )
    projects = (leader_projects | member_projects).distinct()

    unread_count = 0
    unread_chat_counts = {}
    pending_tasks_counts = {}
    pending_tasks_counts1 = {}
    all_tasks_counts = {}
    progress_percentages = {}
    total_progress_percentages = {}

    all_unread_chats = []
    all_pending_tasks = []
    all_tasks = []

  # Calculate unread chat statuses and pending tasks for each project
    for project in projects:
        try:
            group_chat = GroupChat.objects.get(project=project)
            chats = Chat.objects.filter(group_id=group_chat.group_id).exclude(sender_user_id=request.user.id)
            chatstatus = ChatStatus.objects.filter(status=1, user_id=request.user.id)
            all_unread_chats = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
                chatstatus__status=1,
            )
            all_unread_chats1 = chats.filter(
                message__in=chats.values_list('message', flat=True),
                timestamp__in=chats.values_list('timestamp', flat=True),
            )            
            all_unread_chats1 = chatstatus
            unread_chat_counts[project.project_id] = all_unread_chats1.count()     
            unread_count = all_unread_chats1.count() 
        except GroupChat.DoesNotExist:
            unread_chat_counts[project.project_id] = 0  
            unread_count = 0                    

        all_pending_tasks = Tasks.objects.filter(
            project=project,
            is_deleted=0,
        ).exclude(
            task_status='Ongoing',
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
        'now': localtime(now),
        'fname': user.first_name,
        'image': profile.profile_picture.url if profile.profile_picture else None,
        'MEDIA_URL': settings.MEDIA_URL,
        'unread_chat_counts': unread_chat_counts,
        'all_unread_chats': all_unread_chats,
        'all_pending_tasks': all_pending_tasks,
        'pending_tasks_counts': pending_tasks_counts,
        'unread_count': unread_count,
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
            Users.objects.filter(email_address=user.email).update(online=1, logged_in=timezone.now())

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
        user.deleted_at = timezone.now()
        user.save()
        messages.success(request, 'User has been deactivated successfully.')
    return redirect('user_logout')

def user_logout(request):
    user = request.user
    Users.objects.filter(email_address=user.email).update(online=0,logged_out=timezone.now())
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