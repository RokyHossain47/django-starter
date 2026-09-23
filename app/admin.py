from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Setting, Role


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_company_name')

    def get_company_name(self, instance):
        return instance.profile.company_name if hasattr(instance, 'profile') else '-'
    get_company_name.short_description = 'Company'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'company_name', 'phone')


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_public', 'updated_at')
    search_fields = ('key', 'value', 'description')
    list_filter = ('is_public',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
