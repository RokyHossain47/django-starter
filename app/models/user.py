from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    role = models.ForeignKey('app.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Profile)
def sync_profile_role_group(sender, instance, **kwargs):
    if instance.user:
        from django.contrib.auth.models import Group
        if instance.role and instance.role.group:
            instance.user.groups.add(instance.role.group)
            other_role_groups = Group.objects.filter(custom_role__isnull=False).exclude(id=instance.role.group.id)
            instance.user.groups.remove(*other_role_groups)
        elif not instance.role:
            role_groups = Group.objects.filter(custom_role__isnull=False)
            instance.user.groups.remove(*role_groups)

