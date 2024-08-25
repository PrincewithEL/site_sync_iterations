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
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('home1/', views.home1, name='home1'),
    path('client/', views.client, name='client'),
    path('logout/', views.user_logout, name='logout'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/viewchat', views.chat, name='chat'),
    path('projects/<int:pk>/resources', views.resources, name='resources'),
    path('projects/<int:pk>/addresource/', views.add_resource, name='add_resource'),
    path('projects/<int:pk>/deleteresource/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('projects/<int:pk>/tasks&events', views.tasks_events, name='tasks_events'),
    path('projects/<int:pk>/addtask/', views.add_task, name='add_task'),
    path('projects/<int:pk>/deletetask/<int:task_id>/', views.delete_task, name='delete_task'),
    path('projects/<int:pk>/completetask/<int:task_id>/', views.complete_task, name='complete_task'),
    path('projects/<int:pk>/addevent/', views.add_event, name='add_event'),
    path('projects/<int:pk>/deleteevent/<int:event_id>/', views.delete_event, name='delete_event'),
    path('projects/<int:pk>/deletemessage/', views.delete_message, name='delete_message'),
    path('projects/<int:pk>/deleteproject/', views.delete_project, name='delete_project'),
    path('projects/<int:pk>/update/', views.update_project, name='update_project'),
    path('projects/<int:pk>/addprojectmember/', views.add_project_member, name='add_project_member'),
    path('projects/<int:pk>/sendmessage/', views.send_message, name='send_message'),
    path('projects/<int:pk>/removeprojectmember/', views.remove_project_member, name='remove_project_member'),
    path('projects/updateprojectinvitation/', views.update_project_member, name='update_project_member'),
    path('projects/<int:pk>/transactions', views.transactions, name='transactions'),
    path('projects/<int:pk>/addtransaction/', views.add_transaction, name='add_transaction'),
    path('projects/<int:pk>/deletetransaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('projects/<int:pk>/edit_message/', views.edit_message, name='edit_message'),
    path('profile/', views.profile, name='profile'),
    path('deleteuser/', views.delete_user, name='delete_user'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('verify-otp/', views.verify_otp1, name='verify_otp1'),
 ]

if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
