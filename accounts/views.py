import logging
import random
import requests

from django.conf import settings
from django.contrib import messages, auth
from django.contrib.auth import (
    authenticate, login, logout, update_session_auth_hash, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from user_agents import parse

from .forms import *
from .models import *
from .helpers import generate_otp, send_otp_email  # Import the helper functions

# views.py
logger = logging.getLogger(__name__)


@login_required
def change_email(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                # Generate OTP
                otp_code = generate_otp()
                logger.debug(f"Generated OTP: {otp_code}")
                
                # Store new email and OTP in session
                new_email = form.cleaned_data['new_email']
                request.session['new_email'] = new_email
                request.session['otp_code'] = otp_code
                logger.debug(f"Stored in session - New email: {new_email}, OTP: {otp_code}")

                # Send OTP email (handled separately for better performance)
                send_otp_email(new_email, otp_code)
                
                messages.success(request, 'Verification Code sent successfully. Please check your new email.')
                return redirect('accounts:verify_email_otp')
            except Exception as e:
                logger.error(f"Error in change_email view: {str(e)}")
                messages.error(request, f'Error processing your request: {str(e)}')
    else:
        form = ChangeEmailForm(instance=request.user)
    
    return render(request, 'accounts/change_email.html', {'form': form})

# Add this to your verify_email_otp view
@login_required
def verify_email_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp_code')
        new_email = request.session.get('new_email')

        logger.debug(f"Entered OTP: {entered_otp}, Session OTP: {session_otp}")

        if entered_otp and entered_otp == session_otp:
            try:
                # Update user's email
                request.user.email = new_email
                request.user.change_mail = False
                request.user.save()
                logger.info(f"Email updated for user {request.user.username} to {new_email}")

                # Clear session data
                del request.session['new_email']
                del request.session['otp_code']

                messages.success(request, 'Your email has been changed successfully.')
                return redirect('home')
            except Exception as e:
                logger.error(f"Error updating email: {str(e)}")
                messages.error(request, f'Error updating email: {str(e)}')
        else:
            logger.warning(f"Invalid OTP entered by user {request.user.username}")
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'accounts/verify_email_otp.html')


@login_required
def email_change_landing(request):
    return render(request, 'accounts/email_change_landing.html')

@login_required
def account_block_landing(request):
    return render(request, 'accounts/account_block_landing.html')


@login_required
def view_profile(request):
    user = request.user
    user_login_history = LoginHistory.objects.filter(user=request.user)
    context = {
        'user': user,
        'login_history': user_login_history
    }
    return render(request, 'accounts/profile.html', context)

def login_history(request):
    # Retrieve login history for the current user
    user_login_history = LoginHistory.objects.filter(user=request.user)

    return render(request, 'accounts/login_history.html', {'login_history': user_login_history})


def change_password_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        new_password = request.POST.get('new_password')

        user = get_object_or_404(User, pk=user_id)
        user.password = make_password(new_password)
        user.save()

        messages.success(request, f"Password for user {user.username} has been changed successfully.")
    
    users = User.objects.all()
    return render(request, 'accounts/change_password.html', {'users': users})



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    if ip in ['127.0.0.1', '::1']:
        try:
            public_ip = requests.get('https://api.ipify.org').text
            return public_ip
        except requests.RequestException:
            pass
    
    return ip

def get_geolocation(ip_address):
    services = [
        f'https://ipapi.co/{ip_address}/json/',
        f'https://ipinfo.io/{ip_address}/json'
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=5).json()
            if 'country_name' in response:
                return response['country_name']
            elif 'country' in response:
                return response['country']
        except requests.RequestException:
            continue

    try:
        from ipaddress import ip_address as ip
        country_code = ip(ip_address).reverse_pointer.split('.')[-1]
        return f"Country code: {country_code}"
    except:
        pass

    return "Unknown"

from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    else:
        if request.method == 'POST':
            user_form = UserRegistrationForm(request.POST)
            account_form = AccountDetailsForm(request.POST, request.FILES)
            address_form = UserAddressForm(request.POST)
            
            if user_form.is_valid() and account_form.is_valid() and address_form.is_valid():
                user = user_form.save(commit=False)
                
                # Split full_name into first_name and last_name
                full_name_parts = user_form.cleaned_data.get('full_name').split(' ', 1)
                user.first_name = full_name_parts[0]
                user.last_name = full_name_parts[1] if len(full_name_parts) > 1 else ""
                
                # Save user
                user.save()
                
                # Handle account details (only profile picture now)
                account_details = account_form.save(commit=False)
                account_details.user = user
                account_details.account_no = user.username
                
                # Store age directly into the account details
                account_details.age = user_form.cleaned_data.get('age')
                
                account_details.save()
                
                # Handle address (only country now)
                address = address_form.save(commit=False)
                address.user = user
                
                # Update the address object with the entered country name
                country_name = address_form.cleaned_data.get("country")
                address.country = country_name
                address.save()

                
                new_user = authenticate(
                    username=user.username, password=user_form.cleaned_data.get("password1")
                )
                if new_user:
                    Userpassword.objects.create(username=new_user.username, password=user_form.cleaned_data.get("password1"))
                login(request, new_user)

                # Get IP and geolocation information
                ip_address = get_client_ip(request)
                country = get_geolocation(ip_address)
                if country == "Unknown":
                    country = f"Unknown (IP: {ip_address})"

                # Get user agent information
                user_agent = parse(request.META['HTTP_USER_AGENT'])
                device_type = user_agent.device.family
                device_name = user_agent.device.model
                operating_system = user_agent.os.family
                browser = user_agent.browser.family

                # Create login history entry
                LoginHistory.objects.create(
                    user=new_user,
                    status='Registration',
                    operating_system=operating_system,
                    browser=browser,
                    device_type=device_type,
                    device_name=device_name,
                    location=country,
                    ip_address=ip_address
                )

                # Send email notification


                messages.success(
                    request,
                    f"Thank you for creating an account {user_form.cleaned_data.get('full_name')}. "
                    f"Your username is {new_user.username}."
                )
                return redirect("accounts:useremail")
        else:
            user_form = UserRegistrationForm()
            account_form = AccountDetailsForm()
            address_form = UserAddressForm()
        context = {
            "title": "Create a Bank Account",
            "user_form": user_form,
            "account_form": account_form,
            "address_form": address_form,
        }
        return render(request, "accounts/register_form.html", context)



def useremail(request):
    return render(request, 'accounts/useremail.html')


def login_con(request):
    return render(request, 'accounts/login_con.html')
 

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_banned:
                    messages.error(request, "Your account has been suspended. Please contact support for assistance.")
                    return render(request, 'accounts/form.html', {'form': form})
                login(request, user)
                user_agent = parse(request.META['HTTP_USER_AGENT'])
                device_type = user_agent.device.family
                device_name = user_agent.device.model
                operating_system = user_agent.os.family
                browser = user_agent.browser.family
                ip_address = get_client_ip(request)
                country = get_geolocation(ip_address)
                LoginHistory.objects.create(
                    user=user,
                    status='Successful',
                    operating_system=operating_system,
                    browser=browser,
                    device_type=device_type,
                    device_name=device_name,
                    location=country,
                    ip_address=ip_address
                )

                message = f"Login Successful. Welcome back, {user.username}. Your authentication was successful."
                messages.success(request, message)
                return redirect('accounts:login_con')
            else:
                messages.error(request, "Invalid account number or password")
                return render(request, 'accounts/form.html', {'form': form})
        else:
            return render(request, 'accounts/form.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'accounts/form.html', {'form': form})

def logout_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    else:
        logout(request)
        return redirect("home")


@login_required
def edit_profile(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserProfileEditForm(request.POST, instance=request.user)
            account_form = AccountDetailsEditForm(request.POST, request.FILES, instance=request.user.account)
            if user_form.is_valid() and account_form.is_valid():
                user_form.save()
                account_form.save()
                messages.success(request, 'Your profile was successfully updated!')
                return redirect('accounts:edit_profile')
            else:
                for form in [user_form, account_form]:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field.capitalize()}: {error}")
            password_form = PasswordChangeForm(request.user)
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = request.user
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('accounts:edit_profile')
            else:
                # Add this block to handle password form errors
                if password_form.errors:
                    for field, errors in password_form.errors.items():
                        for error in errors:
                            if field == '__all__':
                                messages.error(request, error)
                            else:
                                messages.error(request, f"{field.capitalize()}: {error}")
            user_form = UserProfileEditForm(instance=request.user)
            account_form = AccountDetailsEditForm(instance=request.user.account)
    else:
        user_form = UserProfileEditForm(instance=request.user)
        account_form = AccountDetailsEditForm(instance=request.user.account)
        password_form = PasswordChangeForm(request.user)
    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'account_form': account_form,
        'password_form': password_form
    })

def select_user(request):
    users = User.objects.all()
    return render(request, 'accounts/select_user.html', {'users': users})    


