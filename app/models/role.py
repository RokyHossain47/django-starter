from django.db import models
from django.contrib.auth.models import Group, Permission


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
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
