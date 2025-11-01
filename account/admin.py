from django.contrib import admin
from account.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import EmailOTP

class UserModelAdmin(BaseUserAdmin):
    
    list_display = ['id','email', 'name','tc', 'is_admin']
    list_filter = ['is_admin']
    fieldsets = [
        ('User Credentials', {'fields': ['email', 'password']}),
        ('Personal info', {'fields': ['name','tc']}),
        ('Permissions', {'fields': ['is_admin']}),
    ]
 
    add_fieldsets = [
        (
            None, {
                'classes': ['wide'],
                'fields': ['email', 'name','tc', 'password1', 'password2'],
            }),
    ]
    search_fields = ['email']
    ordering = ['email','id']
    filter_horizontal = []


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "purpose", "used", "created_at", "expires_at")
    search_fields = ("user__email", "otp")

# Now register the new UserModelAdmin...
admin.site.register(User, UserModelAdmin)