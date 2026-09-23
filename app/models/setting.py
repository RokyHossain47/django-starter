from django.db import models


class Setting(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="Unique configuration key identifier")
    value = models.TextField(blank=True, null=True, help_text="Configuration value")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="Brief description of this setting")
    is_public = models.BooleanField(default=False, help_text="Whether this setting is accessible publicly")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']

    def __str__(self):
        return self.key

    @classmethod
    def get_value(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
            return setting.value if setting.value is not None else default
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description=None, is_public=False):
        setting, created = cls.objects.get_or_create(key=key)
        setting.value = value
        if description is not None:
            setting.description = description
        setting.is_public = is_public
        setting.save()
        return setting
