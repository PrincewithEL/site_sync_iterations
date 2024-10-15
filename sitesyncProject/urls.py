"""
URL configuration for sitesyncProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from sitesyncApp import views
from django.conf import settings
from sitesyncApp.views import get_chatbot_response
from sitesyncApp.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('admin1/', views.admin1, name='admin1'),
    path('', views.home, name='home'),
    path('auth/', include('social_django.urls', namespace='social')), 
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('google_signup/', views.google_signup, name='google_signup'),
    path('signup/', views.signup, name='signup'),
    path('prototype/', views.prototype, name='prototype'),
    path('signin/', views.signin, name='signin'),
    path('projects/<int:project_id>/signin/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='signin'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('home1/', views.home1, name='home1'),
    path('client/', views.client, name='client'),
    path('logout/', views.user_logout, name='logout'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/viewchat', views.chat, name='chat'),
    path('projects/<int:pk>/resources', views.resources, name='resources'),
    path('projects/<int:pk>/dashboard', views.dashboard, name='dashboard'),    
    path('projects/<int:pk>/addresource/', views.add_resource, name='add_resource'),
    path('projects/<int:pk>/deleteresource/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('projects/<int:pk>/deleteresource/', views.delete_resources, name='delete_resources'),
    path('projects/<int:pk>/restoreresource/<int:resource_id>/', views.restore_resource, name='restore_resource'),
    path('projects/<int:pk>/hideresource/<int:resource_id>/', views.hide_resource, name='hide_resource'),
    path('projects/<int:pk>/tasks', views.tasks, name='tasks'),
    path('projects/<int:pk>/tasks/gantt', views.gantt, name='gantt'),
    path('task/update/<int:task_id>/', views.update_task, name='update_task'),
    path('projects/<int:project_id>/tasks1/', views.tasks1, name='tasks1'),
    path('projects/<int:pk>/events', views.events, name='events'),
    path('projects/<int:pk>/addtask/', views.add_task, name='add_task'),
    path('projects/<int:pk>/deletetask/<int:task_id>/', views.delete_task, name='delete_task'),
    path('projects/<int:pk>/completetask/<int:task_id>/', views.complete_task, name='complete_task'),
    path('projects/<int:pk>/addevent/', views.add_event, name='add_event'),
    path('projects/<int:pk>/deleteevent/<int:event_id>/', views.delete_event, name='delete_event'),
    path('projects/<int:pk>/deletemessage/', views.delete_message, name='delete_message'),
    path('projects/<int:pk>/deleteproject/', views.delete_project, name='delete_project'),
    path('projects/<int:pk>/restoreproject/', views.restore_project, name='restore_project'),
    path('projects/<int:pk>/hideproject/', views.hide_project, name='hide_project'),
    path('projects/<int:pk>/update/', views.update_project, name='update_project'),
    path('projects/<int:pk>/addprojectmember/', views.add_project_member, name='add_project_member'),
    path('projects/<int:pk>/sendmessage/', views.send_message, name='send_message'),
    path('projects/<int:pk>/removeprojectmember/', views.remove_project_member, name='remove_project_member'),
    path('projects/<int:pk>/exitproject/', views.exit_project, name='exit_project'),
    path('projects/updateprojectinvitation/', views.update_project_member, name='update_project_member'),
    path('projects/<int:pk>/transactions', views.transactions, name='transactions'),
    path('projects/<int:pk>/addtransaction/', views.add_transaction, name='add_transaction'),
    path('projects/<int:pk>/deletetransaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('projects/<int:pk>/restoretransaction/<int:transaction_id>/', views.restore_transaction, name='restore_transaction'),
    path('projects/<int:pk>/hidetransaction/<int:transaction_id>/', views.hide_transaction, name='hide_transaction'),
    path('projects/<int:pk>/restoreevent/<int:event_id>/', views.restore_event, name='restore_event'),
    path('projects/<int:pk>/hideevent/<int:event_id>/', views.hide_event, name='hide_event'), 
    path('projects/<int:pk>/restoretask/<int:task_id>/', views.restore_task, name='restore_task'),
    path('projects/<int:pk>/hidetask/<int:task_id>/', views.hide_task, name='hide_task'),        
    path('projects/<int:pk>/edit_message/', views.edit_message, name='edit_message'),
    path('profile/', views.profile, name='profile'),
    path('deleteuser/', views.delete_user, name='delete_user'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('verify-otp/', views.verify_otp1, name='verify_otp1'),
    path('get-response/', get_chatbot_response, name='get_chatbot_response'),
    path('project/<int:project_id>/pin_message/', views.pin_message, name='pin_message'),
    path('project/<int:project_id>/unpin_message/', views.unpin_message, name='unpin_message'),
    path('project/<int:project_id>/bookmark_message/', views.bookmark_message, name='bookmark_message'),
    path('project/<int:project_id>/unbookmark_message/', views.unbookmark_message, name='unbookmark_message'),
    path('reply/<int:pk>/', views.reply_message, name='reply_message'),

    #APIs

    path('api/signin/', SignInView.as_view(), name='signin_api'),
    path('api/logout/', LogOutView, name='logout_api'),
    path('api/signup/', SignUpView, name='signup_api'),
    path('api/completeprofile/', CompleteProfileView, name='complete_profile_api'),      
    path('api/verifyotp/', VerifyOtpView, name='verify_otp_api'), 
    path('api/client-projects/', ClientProjectsAPI.as_view(), name='client-projects-api'),     
    path('api/create-project/', create_project, name='create_project'),
    path('api/forgot-password/', ForgotPasswordAPI.as_view(), name='forgot_password_api'),
    path('api/verify-otp/', VerifyOtpAPI.as_view(), name='verify_otp_api'),
    path('api/verify-otp1/', VerifyOtp1API.as_view(), name='verify_otp1_api'),
    path('api/reset-password/', ResetPasswordAPI.as_view(), name='reset_password_api'),
    path('api/add-project-member/<int:pk>/', add_project_member_api, name='add_project_member_api'),
    path('api/project/<int:pk>/remove_member/', remove_project_member_api, name='remove_project_member_api'),
    path('api/project/<int:pk>/exit/', exit_project_api, name='exit_project_api'),
    path('api/profile/', api_view_profile, name='api_view_profile'),
    path('api/profile/update/', api_update_profile, name='api_update_profile'),
    path('api/chat/<int:pk>/', chat_room_view, name='chat_room_view'),
    path('api/send-message/<int:pk>/', send_message_api, name='send_message_api'),
    path('api/edit-message/<int:pk>/', EditMessageAPIView.as_view(), name='edit_message_api'),
    path('api/delete-message/<int:pk>/', DeleteMessageAPIView.as_view(), name='delete_message_api'),
    path('api/projects/<int:pk>/resources/', ResourceListView.as_view(), name='resource-list'),
    path('api/project/<int:project_id>/project-members/', get_potential_project_members, name='project-members-list'),
    path('api/project/<int:pk>/', ProjectDetailAPI.as_view(), name='project-detail-api'),    
    path('api/projects/<int:pk>/resources/add/', AddResourceView.as_view(), name='api_add_resource'),
    path('api/projects/<int:pk>/resources/delete/<int:resource_id>/', DeleteResourceView.as_view(), name='api_delete_resource'),
    path('api/projects/<int:pk>/tasks/', TaskListView.as_view(), name='tasks-list'),
    path('api/projects/<int:pk>/tasks/add/', AddTaskAPIView.as_view(), name='add_task_api'),
    path('api/projects/<int:pk>/tasks/<int:task_id>/delete/', DeleteTaskAPIView.as_view(), name='delete_task_api'),
    path('api/projects/<int:pk>/tasks/<int:task_id>/complete/', CompleteTaskAPIView.as_view(), name='complete_task_api'),
    path('api/projects/<int:pk>/resources/<int:resource_id>/restore/', RestoreResourceAPI.as_view(), name='restore_resource'),
    path('api/projects/<int:pk>/resources/<int:resource_id>/hide/', HideResourceAPI.as_view(), name='hide_resource'),
    path('api/projects/<int:pk>/delete/', DeleteProjectAPI.as_view(), name='delete_project'),
    path('api/projects/<int:pk>/restore/', RestoreProjectAPI.as_view(), name='restore_project'),
    path('api/projects/<int:pk>/hide/', HideProjectAPI.as_view(), name='hide_project'),
    path('api/projects/<int:pk>/tasks/<int:task_id>/restore/', RestoreTaskAPI.as_view(), name='restore_task'),
    path('api/projects/<int:pk>/tasks/<int:task_id>/hide/', HideTaskAPI.as_view(), name='hide_task'),
    path('api/projects/<int:pk>/transactions/', TransactionViewSet.as_view({'get': 'list', 'post': 'create'}), name='project-transactions'),
    path('api/projects/<int:pk>/transactions/<int:event_id>/', TransactionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='project-transaction-detail'),
    path('api/projects/<int:pk>/events/', EventViewSet.as_view({'get': 'list', 'post': 'add'}), name='project-events'),
    path('api/projects/<int:pk>/events/<int:event_id>/', EventViewSet.as_view({'delete': 'delete'}), name='project-event-detail'),
 ]

if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
