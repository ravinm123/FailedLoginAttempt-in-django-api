from django.contrib import admin
from django.urls import path
from .models import User,FailedLoginAttempt
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponse

# Register your models here.
class UserModelAdmin(BaseUserAdmin):
  # The fields to be used in displaying the User model.
  # These override the definitions on the base UserModelAdmin
  # that reference specific fields on auth.User.
  list_display = ('email', 'name','is_admin')
  list_filter = ('is_admin',)
  fieldsets = (
      ('User Credentials', {'fields': ('email', 'password')}),
      ('Personal info', {'fields': ('name',)}),
      ('Permissions', {'fields': ('is_admin',)}),
  )
  # add_fieldsets is not a standard ModelAdmin attribute. UserModelAdmin
  # overrides get_fieldsets to use this attribute when creating a user.
  add_fieldsets = (
      (None, {
          'classes': ['wide'],
          'fields': ['email', 'name', 'password1', 'password2'],
      }),
  )
  search_fields = ('email',)
  ordering = ['email']
  filter_horizontal = ()
  
def reset_password(self, request, queryset):
        """Custom admin action to reset user passwords."""
        for user in queryset:
            # Update user fields before password reset
            failed_attempts = FailedLoginAttempt.objects.filter(user=user).first()
            if failed_attempts and failed_attempts.locked:
                # Set fields for the user
                user.locked = False
                user.password_change_required = True
                user.save()

                # Reset the password
                form = SetPasswordForm(user)
                form.save()  # Optionally: Provide a new password or reset it to a default one

                # Reset failed login attempts
                failed_attempts.attempts = 0
                failed_attempts.save()

                self.message_user(request, f'Password for {user.email} has been reset and account unlocked.')
            else:
                self.message_user(request, f'{user.email} is not locked or not eligible for reset.')

reset_password.short_description = ('Reset Password')


# Now register the new UserModelAdmin...
admin.site.register(User, UserModelAdmin)

class FailedLoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'attempts', 'last_attempt', 'locked')
    list_filter = ('locked', 'last_attempt')
    search_fields = ('user__email',)
    
    def reset_password(self, request, queryset):
        # Similar implementation as above
        pass

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('locked/', self.admin_site.admin_view(self.locked_users_view), name='locked_users')
        ]
        return custom_urls + urls

    def locked_users_view(self, request):
        locked_users = User.objects.filter(failedloginattempt__locked=True)
        # Render or return response with locked users
        return HttpResponse("Locked Users: " + ", ".join(user.email for user in locked_users))
    
#     def reset_password(self, request, queryset):
#         for user in queryset:
#             failed_attempts = FailedLoginAttempt.objects.filter(user=user).first()
#             if failed_attempts and failed_attempts.locked:
#                     # Reset the user's password
#                 form = SetPasswordForm(user)
#                 form.save()  # Optionally: provide a new password or reset it to a default one
#                 failed_attempts.attempts = 0
#                 failed_attempts.locked = False
#                 failed_attempts.save()
#                 self.message_user(request, f'Password for {user.email} has been reset.')
#             else:
#                 self.message_user(request, f'{user.email} is not locked or not eligible for reset.')

# reset_password.short_description = ('Reset Password')
    
admin.site.register(FailedLoginAttempt,FailedLoginAttemptAdmin)


