# ip_ban/middleware.py
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from .models import IPBan, VisitorLog
from django.utils import timezone
from django.conf import settings

class IPBanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define safe IPs and paths
        self.safe_ips = {
            '127.0.0.1',
            'localhost',
            '::1',  # IPv6 localhost
        }
        self.safe_paths = {
            '/staff/',
            '/admin/',
            '/staff/login/',
            '/admin/login/',
        }

    def __call__(self, request):
        # Get IP address
        ip_address = self.get_client_ip(request)
        
        # Check if this is a safe IP or admin path
        is_safe_ip = ip_address in self.safe_ips
        is_admin_path = any(request.path.startswith(path) for path in self.safe_paths)
        
        # Allow access if it's a safe IP or admin path
        if is_safe_ip or is_admin_path:
            return self.get_response(request)
        
        # Check ban status for non-safe IPs
        is_banned = cache.get(f'ip_ban_{ip_address}')
        
        if is_banned is None:
            # Check database if not in cache
            is_banned = IPBan.objects.filter(
                ip_address=ip_address,
                expires_at__isnull=True
            ).exists() or IPBan.objects.filter(
                ip_address=ip_address,
                expires_at__gt=timezone.now()
            ).exists()
            
            # Cache the result
            cache.set(f'ip_ban_{ip_address}', is_banned, timeout=86400)
        
        if is_banned:
            return HttpResponseForbidden(
                render_to_string('errors/banned.html', {
                    'ip_address': ip_address
                })
            )

        # Get the response
        response = self.get_response(request)
        
        # Log the visit (except for safe paths)
        if not is_admin_path:
            try:
                user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
                
                VisitorLog.objects.create(
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    path=request.path,
                    user=user,
                    method=request.method,
                    referer=request.META.get('HTTP_REFERER', '')
                )
            except Exception as e:
                import logging
                logger = logging.getLogger('django')
                logger.error(f"Error logging visitor: {str(e)}")
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

