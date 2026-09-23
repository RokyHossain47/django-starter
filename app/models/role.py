from django.db import models
from django.contrib.auth.models import Group, Permission, User


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for this role")
    description = models.TextField(blank=True, null=True, help_text="Short description of what this role allows")
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='custom_role', null=True, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='custom_roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure a synchronized Django Group exists for this Role
        if not self.group:
            group, _ = Group.objects.get_or_create(name=f"Role: {self.name}")
            self.group = group
            super().save(update_fields=['group'])
        elif self.group.name != f"Role: {self.name}":
            self.group.name = f"Role: {self.name}"
            self.group.save(update_fields=['name'])

    def sync_to_group(self):
        """
        Synchronizes all role permissions with the associated Django Auth Group.
        """
        if not self.group:
            group, _ = Group.objects.get_or_create(name=f"Role: {self.name}")
            self.group = group
            self.save(update_fields=['group'])
        
        # Sync permissions to group
        self.group.permissions.set(self.permissions.all())

    def assign_user(self, user):
        """
        Assigns a user to this role, attaches them to the group and profile.
        """
        # Remove user from any previous role groups
        for prev_role in Role.objects.exclude(pk=self.pk).filter(group__isnull=False):
            if prev_role.group:
                user.groups.remove(prev_role.group)
        
        if self.group:
            user.groups.add(self.group)

        if hasattr(user, 'profile'):
            user.profile.role = self
            user.profile.save(update_fields=['role'])
