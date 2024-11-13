from django.contrib import admin
from .models import (
    Bookmarks, Chat, ChatStatus, Events, GroupChat, ProjectMembers, Projects,
    Resources, Tasks, Transactions, Users, Profile, OTP, AuthGroup, AuthGroupPermissions,
    AuthPermission, AuthUser, AuthUserGroups, AuthUserUserPermissions, DjangoAdminLog,
    DjangoContentType, DjangoMigrations, DjangoSession
)
from django.utils import timezone
from django.db import models

@admin.register(Bookmarks)
class BookmarksAdmin(admin.ModelAdmin):
    pass

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    pass

@admin.register(ChatStatus)
class ChatStatusAdmin(admin.ModelAdmin):
    pass

@admin.register(Events)
class EventsAdmin(admin.ModelAdmin):
    pass

@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    pass

@admin.register(ProjectMembers)
class ProjectMembersAdmin(admin.ModelAdmin):
    pass

@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    pass

@admin.register(Resources)
class ResourcesAdmin(admin.ModelAdmin):
    pass

@admin.register(Tasks)
class TasksAdmin(admin.ModelAdmin):
    pass

@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    pass

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    pass

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    pass

@admin.register(AuthGroup)
class AuthGroupAdmin(admin.ModelAdmin):
    pass

@admin.register(AuthGroupPermissions)
class AuthGroupPermissionsAdmin(admin.ModelAdmin):
    pass

@admin.register(AuthPermission)
class AuthPermissionAdmin(admin.ModelAdmin):
    pass

@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    pass

@admin.register(AuthUserGroups)
class AuthUserGroupsAdmin(admin.ModelAdmin):
    pass

@admin.register(AuthUserUserPermissions)
class AuthUserUserPermissionsAdmin(admin.ModelAdmin):
    pass

@admin.register(DjangoAdminLog)
class DjangoAdminLogAdmin(admin.ModelAdmin):
    pass

@admin.register(DjangoContentType)
class DjangoContentTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(DjangoMigrations)
class DjangoMigrationsAdmin(admin.ModelAdmin):
    pass

@admin.register(DjangoSession)
class DjangoSessionAdmin(admin.ModelAdmin):
    pass