from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

User = settings.AUTH_USER_MODEL

# middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
import logging


# middleware.py

logger = logging.getLogger(__name__)

class AccountRestrictionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.debug(f"Processing request for user {request.user.username}")
            if request.user.change_mail:
                allowed_paths = [
                    reverse('accounts:email_change_landing'),
                    reverse('accounts:change_email'),
                    reverse('accounts:verify_email_otp')
                ]
                if request.path not in allowed_paths:
                    logger.info(f"Redirecting user {request.user.username} to email change landing")
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'redirect_url': reverse('accounts:email_change_landing')}, status=403)
                    return redirect('accounts:email_change_landing')
            
            elif request.user.account_block:
                allowed_paths = [
                    reverse('accounts:account_block_landing'),
                    reverse('transactions:ticket')
                ]
                if request.path not in allowed_paths:
                    logger.info(f"Redirecting user {request.user.username} to account block landing")
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'redirect_url': reverse('accounts:account_block_landing')}, status=403)
                    return redirect('accounts:account_block_landing')



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}