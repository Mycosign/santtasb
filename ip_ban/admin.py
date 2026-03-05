

from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from .models import IPBan, VisitorLog
from django.db.models import Count
from django.utils import timezone
from django.core.cache import cache

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'timestamp','ban_status_and_action', 'user_agent', 'visit_count', 'path' )
    list_filter = ('timestamp', 'method')
    search_fields = ('ip_address', 'path', 'user_agent')
    date_hierarchy = 'timestamp'
    actions = ['ban_selected_ips']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Annotate each IP with its visit count
        queryset = queryset.annotate(
            total_visits=Count('ip_address')
        )
        return queryset

    def visit_count(self, obj):
        return obj.total_visits
    visit_count.short_description = 'Total Visits'

    def ban_status_and_action(self, obj):
        is_banned = IPBan.objects.filter(ip_address=obj.ip_address).exists()
        if is_banned:
            ban_record = IPBan.objects.get(ip_address=obj.ip_address)
            unban_url = reverse('admin:unban-ip', args=[obj.ip_address])
            return format_html(
                '<span style="color: red;">Banned</span> on {} &nbsp;'
                '<a class="button" style="background-color: #28a745; color: white; '
                'padding: 5px 10px; border-radius: 3px; text-decoration: none;" '
                'href="{}">Unban</a>',
                ban_record.banned_at.strftime('%Y-%m-%d %H:%M'),
                unban_url
            )
        else:
            ban_url = reverse('admin:ban-ip', args=[obj.ip_address])
            return format_html(
                '<a class="button" style="background-color: #d9534f; color: white; '
                'padding: 5px 10px; border-radius: 3px; text-decoration: none;" '
                'href="{}">Ban this IP</a>',
                ban_url
            )
    ban_status_and_action.short_description = 'Ban Status/Action'
    ban_status_and_action.allow_tags = True

    def ban_selected_ips(self, request, queryset):
        ip_addresses = queryset.values_list('ip_address', flat=True).distinct()
        count = 0
        for ip in ip_addresses:
            if not IPBan.objects.filter(ip_address=ip).exists():
                IPBan.objects.create(
                    ip_address=ip,
                    reason=f"Bulk ban via admin action by {request.user}",
                    user_agent=VisitorLog.objects.filter(ip_address=ip).latest('timestamp').user_agent
                )
                count += 1
        messages.success(request, f'Successfully banned {count} IP addresses')
    ban_selected_ips.short_description = "Ban selected IP addresses"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('ban-ip/<str:ip_address>/',
                self.admin_site.admin_view(self.ban_ip),
                name='ban-ip'),
            path('unban-ip/<str:ip_address>/',
                self.admin_site.admin_view(self.unban_ip),
                name='unban-ip'),
        ]
        return custom_urls + urls

    def ban_ip(self, request, ip_address):
        try:
            IPBan.objects.create(
                ip_address=ip_address,
                reason=f"Banned via admin action by {request.user}",
                user_agent=VisitorLog.objects.filter(ip_address=ip_address).latest('timestamp').user_agent
            )
            messages.success(request, f'Successfully banned IP address: {ip_address}')
        except Exception as e:
            messages.error(request, f'Error banning IP: {str(e)}')
        return HttpResponseRedirect(reverse('admin:ip_ban_visitorlog_changelist'))

    def unban_ip(self, request, ip_address):
        try:
            # Delete from database
            IPBan.objects.filter(ip_address=ip_address).delete()
            
            # Clear ban from cache in multiple ways to ensure it's gone
            cache_keys = [
                f'ip_ban_{ip_address}',
                f'ip_ban_{ip_address.replace(".", "_")}',  # Alternative format some systems might use
            ]
            
            # Clear specific ban cache keys
            for key in cache_keys:
                cache.delete(key)
                # Explicitly set to False to ensure middleware knows it's unbanned
                cache.set(key, False, timeout=86400)
            
            # Force a cache flush for this IP
            cache.touch(f'ip_ban_{ip_address}')
            
            messages.success(request, f'Successfully unbanned IP address: {ip_address}')
            
            # Clear entire cache as a last resort
            cache.clear()
            
        except Exception as e:
            messages.error(request, f'Error unbanning IP: {str(e)}')
        return HttpResponseRedirect(reverse('admin:ip_ban_visitorlog_changelist'))

@admin.register(IPBan)
class IPBanAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'banned_at', 'expires_at', 'reason', 'recent_visits')
    search_fields = ('ip_address', 'reason')
    list_filter = ('banned_at', 'expires_at')
    actions = ['reset_all_bans']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reset-all-bans/',
                self.admin_site.admin_view(self.reset_all_bans_view),
                name='reset-all-bans'),
        ]
        return custom_urls + urls

    def reset_all_bans_view(self, request):
        try:
            # Store current IP addresses before deletion
            current_ips = list(IPBan.objects.values('ip_address', 'user_agent'))
            
            # Clear all existing bans
            IPBan.objects.all().delete()
            
            # Clear the cache for all banned IPs
            for ip_data in current_ips:
                cache.delete(f'ip_ban_{ip_data["ip_address"]}')
            
            # Recreate bans with fresh timestamps
            for ip_data in current_ips:
                IPBan.objects.create(
                    ip_address=ip_data['ip_address'],
                    user_agent=ip_data['user_agent'],
                    banned_at=timezone.now(),
                    reason=f"Ban reset and renewed by {request.user}"
                )
            
            messages.success(request, f"Successfully reset {len(current_ips)} IP bans with fresh timestamps.")
        except Exception as e:
            messages.error(request, f"Error resetting bans: {str(e)}")
            
        return HttpResponseRedirect(reverse('admin:ip_ban_ipban_changelist'))

    def recent_visits(self, obj):
        count = VisitorLog.objects.filter(
            ip_address=obj.ip_address,
            timestamp__gte=timezone.now() - timezone.timedelta(days=1)
        ).count()
        return f"{count} visits in last 24h"
    recent_visits.short_description = 'Recent Activity'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['reset_bans_button'] = format_html(
            '<a class="button" href="{}" '
            'style="background-color: #d9534f; color: white; '
            'padding: 5px 10px; border-radius: 3px; text-decoration: none; '
            'margin-bottom: 10px; display: inline-block; margin-right: 8px;">'
            'Reset All Bans</a>',
            reverse('admin:reset-all-bans')
        )
        return super().changelist_view(request, extra_context=extra_context)