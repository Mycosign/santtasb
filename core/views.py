from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth

from transactions.models import *
from transactions.forms import *
from bankcard.models import *
from accounts.models import User


def home(request):
    users = User.objects.all()

    if not request.user.is_authenticated:
        return render(request, "core/index.html", {})
    else:
        user = request.user
        deposit = Diposit.objects.filter(user=user)
        deposit_sum = deposit.aggregate(Sum('amount'))['amount__sum']
        withdrawal = Withdrawal.objects.filter(user=user)
        cryptowithdrawal = CryptoWITHDRAW.objects.filter(user=user)
        withdrawal_sum = withdrawal.aggregate(Sum('amount'))['amount__sum']
        interest = Interest.objects.filter(user=user)
        interest_sum = interest.aggregate(Sum('amount'))['amount__sum']
        # Fetch local withdrawals where the user is either the recipient or the sender (3 most recent)
        local_withdrawals_received = LocalWithdrawal.objects.filter(
            recipient_email=user.email
        ).select_related('user', 'user__account').order_by('-timestamp')[:3]

        local_withdrawals_sent = LocalWithdrawal.objects.filter(
            user=user
        ).order_by('-timestamp')[:3]

        card_details_count = CardDetails.objects.filter(user=user).count()
        card_details_counta = CardDetail.objects.filter(user=user).count()

        context = {
            "user": user,
            "deposit": deposit,
            "deposit_sum": deposit_sum,
            "withdrawal": withdrawal,
            "withdrawal_sum": withdrawal_sum,
            "interest": interest,
            "interest_sum": interest_sum,
            "local_withdrawals_received": local_withdrawals_received,  # Add received withdrawals to context
            "local_withdrawals_sent": local_withdrawals_sent,        # Add sent withdrawals to context
            "card_details_count": card_details_count,
            "card_details_counta": card_details_counta,
            "users": users,
            "title": "ROYAL BANK"
        }

        return render(request, "core/transactions.html", context)
    
def index(request):
    return render(request, "core/alternate.html", {}) 

    
def about(request):
    return render(request, "core/about.html", {})  

def service(request):
    return render(request, "core/service.html", {})



def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            # Add a success message
            messages.success(request, 'Your message has been sent successfully.')
            form = ContactForm()  # Reset the form to display an empty form after submission
    else:
        form = ContactForm()

    context = {
        'form': form,
    }

    return render(request, 'core/contact_us.html', context)






@login_required
def confirm(request):
    payment = Withdrawal.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'core/confirm.html', {'payment': payment})


@login_required
def inter_confirm(request):
    payment = Withdrawal_internationa.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'core/inter_confirm.html', {'payment': payment})


def confirm_password(request):
    return render(request, "core/confirm_password.html", {})
