

# ip_ban/models.py
from django.db import models
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model

class IPBan(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    reason = models.TextField(blank=True)
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'IP Ban'
        verbose_name_plural = 'IP Bans'
    
    def __str__(self):
        return f"{self.ip_address} (banned at {self.banned_at})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update cache when ban is saved
        cache.set(f'ip_ban_{self.ip_address}', True, timeout=86400)

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512)
    path = models.CharField(max_length=2000)
    user = models.ForeignKey(
        get_user_model(), 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    referer = models.CharField(max_length=2000, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ip_address} - {self.path} ({self.timestamp})"
