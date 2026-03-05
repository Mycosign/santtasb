from datetime import datetime
from io import BytesIO
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import F, Q
from django.db import models
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from .forms import *
from .models import *



from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags



@login_required
def ticket(request):
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            support_ticket = form.save(commit=False)
            support_ticket.user = request.user
            support_ticket.save()

            # Prepare email content
            user_fullname = request.user.get_full_name()
            user_email = request.user.email
            admin_email = 'Support@san-tandorglobal.online'
            subject = f"New Support Ticket from {user_fullname}"

            # Render HTML template
            html_message = render_to_string('transactions/support_ticket_email.html', {
                'user_fullname': user_fullname,
                'user_email': user_email,
                'ticket_department': support_ticket.tickets,
                'ticket_message': support_ticket.message,
                'ticket_timestamp': support_ticket.timestamp,
            })
            plain_message = strip_tags(html_message)  # Plain text version

            # Send email with HTML content
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [admin_email], html_message=html_message)

            messages.success(request, 'Your support ticket has been submitted successfully.')
            return redirect('transactions:ticket')  # Redirect to the same page (ticket view)
    else:
        form = SupportForm()

    user = request.user
    ticketlist = SUPPORT.objects.filter(user=user).order_by('-id')    
    context = {
        'form': form,
        'ticketlist': ticketlist
    }
    return render(request, 'transactions/ticket.html', context)

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import LoanApplication, LoanDocument
from .forms import LoanApplicationForm, LoanDocumentForm



@login_required
def loan_application_view(request):
    """View for creating a new loan application"""
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            loan_application = form.save(commit=False)
            loan_application.applicant = request.user
            loan_application.save()
            
            messages.success(
                request, 
                f'Thank you! Your loan application {loan_application.reference_number} has been submitted successfully. '
                f'You will receive updates on your application status within 24-48 hours.'
            )
            return redirect('transactions:loan_application_detail', pk=loan_application.pk)
    else:
        form = LoanApplicationForm()
    
    context = {
        'title': 'Apply for a Loan',
        'form': form,
    }
    return render(request, 'transactions/loan_application_form.html', context)


@login_required
def loan_application_list_view(request):
    """View for listing all loan applications of the current user"""
    loan_applications = LoanApplication.objects.filter(applicant=request.user)
    
    context = {
        'title': 'Your Loan Applications',
        'loan_applications': loan_applications,
    }
    return render(request, 'transactions/loan_request.html', context)

from cloudinary.utils import cloudinary_url

# Updated view
@login_required
def loan_application_detail_view(request, pk):
    """View for displaying details of a specific loan application"""
    loan_application = get_object_or_404(LoanApplication, pk=pk, applicant=request.user)
    
    # Handle document upload
    if request.method == 'POST':
        document_form = LoanDocumentForm(request.POST, request.FILES)
        if document_form.is_valid():
            document = document_form.save(commit=False)
            document.loan_application = loan_application
            document.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('transactions:loan_application_detail', pk=loan_application.pk)
    else:
        document_form = LoanDocumentForm()
    
    # Get related documents
    documents = loan_application.documents.all()
    
    # Generate download URLs for each document
    for document in documents:
        if hasattr(document, 'get_download_url'):
            document.download_url = document.get_download_url()
        else:
            # Fallback to the standard URL with download attributes
            document.download_url = document.document_file.url
    
    # Get related payments (if loan is funded)
    payments = loan_application.payments.all() if loan_application.status == 'FUNDED' else None
    
    context = {
        'title': f'Loan Application: {loan_application.reference_number}',
        'loan_application': loan_application,
        'document_form': document_form,
        'documents': documents,
        'payments': payments,
    }
    return render(request, 'transactions/loan_application_detail.html', context)

# views.py - Add this function-based view for document downloads
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import LoanDocument

@login_required
def document_download_view(request, document_id):
    """View for handling document downloads with proper headers"""
    
    # Get the document or return 404
    document = get_object_or_404(LoanDocument, id=document_id)
    
    # Optional: Check if the user has permission to download this document
    if document.loan_application.applicant != request.user:
        return HttpResponse("You don't have permission to access this document", status=403)
    
    # Redirect to the download URL
    download_url = document.get_download_url()
    if not download_url:
        return HttpResponse("Document not found", status=404)
        
    return HttpResponseRedirect(download_url)
    
@login_required
def cancel_loan_application_view(request, pk):
    """View for canceling a loan application"""
    loan_application = get_object_or_404(LoanApplication, pk=pk, applicant=request.user)
    
    # Only allow cancellation if status is PENDING or IN_PROGRESS
    if loan_application.status not in ['PENDING', 'IN_PROGRESS']:
        messages.error(request, 'This loan application cannot be canceled at its current status.')
        
    
    if request.method == 'POST':
        loan_application.status = 'CANCELED'
        loan_application.save()
        messages.success(request, 'Your loan application has been successfully canceled.')
        return redirect('transactions:loan_application_list')
    
    context = {
        'title': 'Cancel Loan Application',
        'loan_application': loan_application,
    }
    return render(request, 'transactions/loan_application_cancel.html', context)


@login_required
def recent_loans(request):
    recent_loans = LoanRequest.objects.order_by()[:10]
    context = {'recent_loans': recent_loans}
    return render(request, 'transactions/loans.html', context)


from django.db.models import F

import cloudinary
import cloudinary.uploader

@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        form = WithdrawalForm(request.POST, request.FILES)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user

            # Check balance
            withdrawal_amount = withdrawal.amount
            account_balance = withdrawal.user.account.balance

            if withdrawal_amount > account_balance:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Insufficient balance'
                })

            # Handle file uploads to Cloudinary
            if 'approval_document' in request.FILES:
                approval_result = cloudinary.uploader.upload(
                    request.FILES['approval_document'],
                    folder='withdrawal_approvals'
                )
                withdrawal.approval_document = approval_result['public_id']

            if 'fee_receipt' in request.FILES:
                fee_result = cloudinary.uploader.upload(
                    request.FILES['fee_receipt'],
                    folder='fee_receipts'
                )
                withdrawal.fee_receipt = fee_result['public_id']

            withdrawal.status = 'pending'
            withdrawal.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Withdrawal request submitted successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form data',
                'errors': form.errors
            })
    else:
        form = WithdrawalForm()
    
    return render(request, 'transactions/form.html', {'form': form})

# views.py

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import LocalWithdrawal
from .forms import LocalWithdrawalForm

User  = get_user_model()  # Get the user model

class LocalWithdrawalView(LoginRequiredMixin, CreateView):
    model = LocalWithdrawal
    form_class = LocalWithdrawalForm
    template_name = 'transactions/new_paym/local_withdrawal.html'

    def get_success_url(self):
        return reverse_lazy('transactions:withdrawal_success') + f'?type=local&id={self.object.id}'

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Check if the user exists with the provided email and account number
        try:
            user = User.objects.get(email=form.cleaned_data['recipient_email'], account__account_no=form.cleaned_data['recipient_account_number'])
        except User.DoesNotExist:
            messages.error(self.request, "No user found with the provided email and account number.")
            return self.form_invalid(form)

        if form.instance.amount > self.request.user.balance:
            messages.error(self.request, "Insufficient funds")
            return self.form_invalid(form)

        messages.success(self.request, "Local withdrawal request submitted successfully")
        return super().form_valid(form)


class PayPalWithdrawalView(LoginRequiredMixin, CreateView):
    model = PayPalWithdrawal
    form_class = PayPalWithdrawalForm
    template_name = 'transactions/new_paym/paypal_withdrawal.html'
    def get_success_url(self):
        return reverse_lazy('transactions:withdrawal_success') + f'?type=paypal&id={self.object.id}'

    def form_valid(self, form):
        form.instance.user = self.request.user
        if form.instance.amount > self.request.user.balance:
            messages.error(self.request, "Insufficient funds")
            return self.form_invalid(form)
        messages.success(self.request, "PayPal withdrawal request submitted successfully")
        return super().form_valid(form)

class SkrillWithdrawalView(LoginRequiredMixin, CreateView):
    model = SkrillWithdrawal
    form_class = SkrillWithdrawalForm
    template_name = 'transactions/new_paym/skrill_withdrawal.html'
    def get_success_url(self):
        return reverse_lazy('transactions:withdrawal_success') + f'?type=skrill&id={self.object.id}'

    def form_valid(self, form):
        form.instance.user = self.request.user
        if form.instance.amount > self.request.user.balance:
            messages.error(self.request, "Insufficient funds")
            return self.form_invalid(form)
        messages.success(self.request, "Skrill withdrawal request submitted successfully")
        return super().form_valid(form)

class RevolutWithdrawalView(LoginRequiredMixin, CreateView):
    model = SkrillWithdrawal
    form_class = RevolutWithdrawalForm
    template_name = 'transactions/new_paym/revo_withdrawal.html'
    def get_success_url(self):
        return reverse_lazy('transactions:withdrawal_success') + f'?type=revolut&id={self.object.id}'

    def form_valid(self, form):
        form.instance.user = self.request.user
        if form.instance.amount > self.request.user.balance:
            messages.error(self.request, "Insufficient funds")
            return self.form_invalid(form)
        messages.success(self.request, "Revolut withdrawal request submitted successfully")
        return super().form_valid(form)


class WiseWithdrawalView(LoginRequiredMixin, CreateView):
    model = SkrillWithdrawal
    form_class = WiseWithdrawalForm
    template_name = 'transactions/new_paym/wise_withdrawal.html'
    def get_success_url(self):
        return reverse_lazy('transactions:withdrawal_success') + f'?type=wise&id={self.object.id}'
    def form_valid(self, form):
        form.instance.user = self.request.user
        if form.instance.amount > self.request.user.balance:
            messages.error(self.request, "Insufficient funds")
            return self.form_invalid(form)
        messages.success(self.request, "Wise withdrawal request submitted successfully")
        return super().form_valid(form)

# views.py

# views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    LocalWithdrawal, 
    PayPalWithdrawal, 
    SkrillWithdrawal,
    RevolutWithdrawal,
    WiseWithdrawal
)

class WithdrawalSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'transactions/withdrawal_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        withdrawal_type = self.request.GET.get('type', '')
        withdrawal_id = self.request.GET.get('id', '')
        
        # Get the transaction details based on withdrawal type
        transaction = None
        if withdrawal_type == 'local':
            transaction = LocalWithdrawal.objects.get(id=withdrawal_id)
        elif withdrawal_type == 'paypal':
            transaction = PayPalWithdrawal.objects.get(id=withdrawal_id)
        elif withdrawal_type == 'skrill':
            transaction = SkrillWithdrawal.objects.get(id=withdrawal_id)
        elif withdrawal_type == 'revolut':
            transaction = RevolutWithdrawal.objects.get(id=withdrawal_id)
        elif withdrawal_type == 'wise':
            transaction = WiseWithdrawal.objects.get(id=withdrawal_id)

        withdrawal_info = {
            'local': {
                'title': 'Local Bank Transfer',
                'message': 'Your local bank transfer request has been submitted successfully.',
                'icon': 'fa-bank'
            },
            'paypal': {
                'title': 'PayPal Withdrawal',
                'message': 'Your PayPal withdrawal request has been submitted successfully.',
                'icon': 'fa-paypal'
            },
            'skrill': {
                'title': 'Skrill Withdrawal',
                'message': 'Your Skrill withdrawal request has been submitted successfully.',
                'icon': 'fa-wallet'
            },
            'revolut': {
                'title': 'Revolut Withdrawal',
                'message': 'Your Revolut withdrawal request has been submitted successfully.',
                'icon': 'fa-exchange'
            },
            'wise': {
                'title': 'Wise Transfer',
                'message': 'Your Wise transfer request has been submitted successfully.',
                'icon': 'fa-globe'
            }
        }

        context.update({
            'withdrawal_info': withdrawal_info.get(withdrawal_type, {}),
            'withdrawal_type': withdrawal_type,
            'transaction': transaction,
            'user': self.request.user
        })
        return context


@login_required
def login_con(request):
    return render(request, 'transactions/login_con.html')

def terms(request):
    return render(request, 'transactions/terms.html')
    
@login_required
def pay_bills(request):
    if request.method == 'POST':
        form = PayBillsForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.user = request.user

            # Check if the bill amount is greater than the account balance
            bill_amount = bill.amount
            account_balance = bill.user.account.balance

            if bill_amount > account_balance:
                # Insufficient balance, form submission is halted
                form.add_error('amount', 'Insufficient balance. You cannot pay more than your account balance.')
            else:
                # Deduct the bill amount from the account balance using F() expression
                #bill.user.account.balance = F('balance') - bill_amount
                bill.user.account.save()

                bill.save()

                # Add a success message with details
                message = f"Thank you, {request.user.username}! Your bill payment for {bill.nickname} has been successfully processed."
                messages.success(request, message)

                return redirect('transactions:bill_con')  # Replace 'bill_con' with the appropriate URL name for the success page
    else:
        form = PayBillsForm()

    context = {
        'form': form,
    }
    return render(request, 'transactions/pay_bills.html', context)


@login_required
def bill_success(request):
    payment = PayBills.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'transactions/bill_success.html', {'payment': payment})

@login_required
def bill_con(request):
    return render(request, 'transactions/bill_con.html')

@login_required
def manage_asset(request):
    if not request.user.is_authenticated:
        return render(request, "core/index.html", {})
    
    user = request.user
    cryptowithdrawals = CryptoWITHDRAW.objects.filter(user=user).order_by('-id')
    cryptowithdra = Payment.objects.filter(user=user).order_by('-id')

    context = {
        "user": user,
        "cryptowithdrawals": cryptowithdrawals,
        "cryptowithdra": cryptowithdra,
        "title": "ROYAL BANK"
    }

    return render(request, 'transactions/manage.html', context)


@login_required
def card_details_upload(request):
    if request.method == 'POST':
        form = CardDetailsForm(request.POST)
        if form.is_valid():
            card_details = form.save(commit=False)
            card_details.user = request.user
            card_details.save()
            messages.success(request, 'Card details uploaded successfully.')  # Add success message
            return redirect('home')
    else:
        form = CardDetailsForm()

    context = {'form': form}
    return render(request, 'transactions/card_upload.html', context)



@login_required
def payment_create(request):
    bank_transfer_methods = BankTransfer.objects.all()  # Fetch all bank transfer objects
    wallets_instance = CRYPWALLETS.objects.first()  # Fetch crypto wallet addresses
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            # Handle wallet address for crypto
            if payment.payment_method in ['BITCOIN', 'ETHEREUM', 'USDT_TRC20']:
                crypto_wallet = {
                    'BITCOIN': wallets_instance.bitcoin,
                    'ETHEREUM': wallets_instance.ethereum,
                    'USDT_TRC20': wallets_instance.tron,
                }.get(payment.payment_method, '')
                return render(request, 'transactions/payment_success.html', {
                    'payment': payment,
                    'crypto_wallet': crypto_wallet,
                })
            return redirect('transactions:payment_success')
        else:
            # Add error handling for invalid form
            error_messages = form.errors.as_json()  # Get form errors in JSON format
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")  # Display each error to the user

    else:
        form = PaymentForm()
    
    return render(request, 'transactions/payment_form.html', {
        'form': form,
        'bank_transfer_methods': bank_transfer_methods,
        'wallets_instance': wallets_instance,
    })


@login_required
def payment_success(request):
    payment = Payment.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'transactions/payment_success.html', {'payment': payment})

def create_withdrawal(request):
    if request.method == 'POST':
        form = CryptoWITHDRAWForm(request.POST)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user

            # Check if the withdrawal amount exceeds the user's balance for the chosen cryptocurrency
            account = withdrawal.user.account

            if withdrawal.payment_method == 'BITCOIN' and withdrawal.amount > account.bitcoins:
                form.add_error('amount', 'Insufficient Bitcoin balance.')
            elif withdrawal.payment_method == 'ETHEREUM' and withdrawal.amount > account.ethereums:
                form.add_error('amount', 'Insufficient Ethereum balance.')
            elif withdrawal.payment_method == 'USDT_ERC20' and withdrawal.amount > account.usdt_erc20s:
                form.add_error('amount', 'Insufficient USDT ERC20 balance.')
            elif withdrawal.payment_method == 'TRON' and withdrawal.amount > account.trons:
                form.add_error('amount', 'Insufficient  Tron balance.')

            elif withdrawal.payment_method == 'RIPPLE' and withdrawal.amount > account.ripples:
                form.add_error('amount', 'Insufficient Ripple balance.')
            elif withdrawal.payment_method == 'STELLAR' and withdrawal.amount > account.stellars:
                form.add_error('amount', 'Insufficient Stellar balance.')
            elif withdrawal.payment_method == 'LITECOIN' and withdrawal.amount > account.litecoins:
                form.add_error('amount', 'Insufficient Litecoin balance.')

            if not form.errors:
                withdrawal.save()
                withdrawal.update_balance()
                return redirect('transactions:crypto_success')  # Replace with your success URL
    else:
        form = CryptoWITHDRAWForm()
    
    return render(request, 'transactions/withdrawal_form.html', {'form': form})


@login_required
def crypto_success(request):
    payment = CryptoWITHDRAW.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'transactions/withdraw_success.html', {'payment': payment})

def recent_withdrawals(request):
    recent_withdrawals = Withdrawal.objects.order_by('-date', '-timestamp')[:10]
    context = {'recent_withdrawals': recent_withdrawals}
    return render(request, 'transactions/withdraw.html', context)



def recent_international_withdrawals(request):
    recent_international_withdrawals = Withdrawal_internationa.objects.order_by('-date', '-timestamp')[:10]
    context = {'recent_international_withdrawals': recent_international_withdrawals}
    return render(request, 'transactions/withdraw_international.html', context)



def recent_payments(request):
    recent_payments = Payment.objects.order_by('-date', '-timestamp')[:10]
    context = {'recent_payments': recent_payments}
    return render(request, 'transactions/payment.html', context)



@login_required
def transaction_history(request):
    user = request.user
    deposit_history = Diposit.objects.filter(user=user).order_by('-timestamp')
    withdrawal_history = Withdrawal.objects.filter(user=user).order_by('-timestamp')
    payment_history = Payment.objects.filter(user=user).order_by('-date')
    crypto_history = CryptoWITHDRAW.objects.filter(user=user).order_by('-date')
    pay_bills = PayBills.objects.filter(user=user).order_by('-timestamp')
    local_withdrawals_sent = LocalWithdrawal.objects.filter(user=user).order_by('-timestamp')
    local_withdrawals_received = LocalWithdrawal.objects.filter(recipient_email=user.email).order_by('-timestamp')
    
    # Add new withdrawal types
    paypal_withdrawals = PayPalWithdrawal.objects.filter(user=user).order_by('-timestamp')
    skrill_withdrawals = SkrillWithdrawal.objects.filter(user=user).order_by('-timestamp')
    revolut_withdrawals = RevolutWithdrawal.objects.filter(user=user).order_by('-timestamp')
    wise_withdrawals = WiseWithdrawal.objects.filter(user=user).order_by('-timestamp')

    context = {
        'deposit_history': deposit_history,
        'withdrawal_history': withdrawal_history,
        'payment_history': payment_history,
        'crypto_history': crypto_history,
        'pay_bills': pay_bills,
        'local_withdrawals_sent': local_withdrawals_sent,
        'local_withdrawals_received': local_withdrawals_received,
        'paypal_withdrawals': paypal_withdrawals,
        'skrill_withdrawals': skrill_withdrawals,
        'revolut_withdrawals': revolut_withdrawals,
        'wise_withdrawals': wise_withdrawals,
    }

    if 'export' in request.GET and request.GET['export'] == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transaction_history.pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []

        # Define the path to the logo and add the logo
        image_path = os.path.join(os.path.abspath(os.path.join(settings.BASE_DIR, 'static')), 'dig73.png')
        logo = Image(image_path, width=120, height=60)
        elements.append(logo)
        elements.append(Spacer(1, 12))

        # Add PDF Title
        styles = getSampleStyleSheet()
        title = Paragraph(f"Transaction History for {user.username}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Table headers with enhanced formatting
        data = [
            ["Ref", "Type", "Scope", "Amount", "Date", "Time", "Method/Details", "Status"],
        ]

        # Date and time formatting function
        def format_datetime(dt):
            return dt.strftime('%d %B %Y'), dt.strftime('%I:%M %p')

        # Deposit History
        for deposit in deposit_history:
            date_str, time_str = format_datetime(deposit.timestamp)
            ref = f"D-{user.id}-{deposit.pk}-{str(user.account_no)[-4:]}"
            data.append([ref, "Deposit", "Transfer", f"{user.account.account_currency} {deposit.amount}", date_str, time_str, deposit.payment_method, deposit.status])

        # Withdrawal History
        for withdrawal in withdrawal_history:
            date_str, time_str = format_datetime(withdrawal.timestamp)
            ref = f"W-{user.id}-{withdrawal.pk}-{str(user.account_no)[-4:]}"
            data.append([ref, "Debit", "Transfer", f"{user.account.account_currency} {withdrawal.amount}", date_str, time_str, withdrawal.recipient_bank_name, withdrawal.status])

        # Payment History (with crypto/gift card/bank transfer details)
        for payment in payment_history:
            date_str, time_str = format_datetime(payment.timestamp)
            ref = f"P-{user.id}-{payment.pk}-{str(user.account_no)[-4:]}"
            if payment.payment_method == 'BANK_TRANSFER':
                details = f"{payment.bank_transfer.method} - {payment.bank_transfer.name_tag}"
            elif payment.payment_method == 'GIFTCARD':
                details = f"Gift Card: {payment.giftcard_type}, Code: {payment.giftcard_code}"
            else:
                # Handle crypto payments with wallets info
                details = f"Crypto: {payment.payment_method}"
            data.append([ref, "Payment", "Transfer", f"{user.account.account_currency} {payment.amount}", date_str, time_str, details, payment.status])

        # Pay Bills History
        for payment in pay_bills:
            date_str, time_str = format_datetime(payment.timestamp)
            ref = f"PB-{user.id}-{payment.pk}-{str(user.account_no)[-4:]}"
            data.append([ref, "Pay Bill", payment.delivery_method, f"{user.account.account_currency} {payment.amount}", date_str, time_str, payment.nickname, payment.status])

        # Add local withdrawals sent to PDF
        for transfer in local_withdrawals_sent:
            date_str, time_str = format_datetime(transfer.timestamp)
            ref = f"LW-{user.id}-{transfer.pk}-{str(user.account_no)[-4:]}"
            data.append([
                ref,
                transfer.transaction_type or "Debit",
                "Local Transfer",
                f"{user.account.account_currency} {transfer.amount}",
                date_str,
                time_str,
                f"To: {transfer.recipient_name}",
                transfer.status
            ])

        # Add local withdrawals received to PDF
        for transfer in local_withdrawals_received:
            date_str, time_str = format_datetime(transfer.timestamp)
            ref = f"LW-{transfer.user.id}-{transfer.pk}-{str(user.account_no)[-4:]}"
            data.append([
                ref,
                transfer.transaction_type or "Credit",
                "Local Transfer",
                f"{user.account.account_currency} {transfer.amount}",
                date_str,
                time_str,
                f"From: {transfer.sender_name}",
                transfer.status
            ])

        # PayPal Withdrawals
        for withdrawal in paypal_withdrawals:
            date_str, time_str = format_datetime(withdrawal.timestamp)
            ref = f"PP-{user.id}-{withdrawal.pk}-{str(user.account_no)[-4:]}"
            data.append([
                ref,
                "Debit",
                "PayPal Withdrawal",
                f"{user.account.account_currency} {withdrawal.amount}",
                date_str,
                time_str,
                f"PayPal: {withdrawal.paypal_email}",
                withdrawal.status
            ])

        # Skrill Withdrawals
        for withdrawal in skrill_withdrawals:
            date_str, time_str = format_datetime(withdrawal.timestamp)
            ref = f"SK-{user.id}-{withdrawal.pk}-{str(user.account_no)[-4:]}"
            data.append([
                ref,
                "Debit",
                "Skrill Withdrawal",
                f"{user.account.account_currency} {withdrawal.amount}",
                date_str,
                time_str,
                f"Skrill: {withdrawal.skrill_email}",
                withdrawal.status
            ])

        # Revolut Withdrawals
        for withdrawal in revolut_withdrawals:
            date_str, time_str = format_datetime(withdrawal.timestamp)
            ref = f"RV-{user.id}-{withdrawal.pk}-{str(user.account_no)[-4:]}"
            data.append([
                ref,
                "Debit",
                "Revolut Withdrawal",
                f"{user.account.account_currency} {withdrawal.amount}",
                date_str,
                time_str,
                f"Revolut: {withdrawal.revolut_email}",
                withdrawal.status
            ])

        # Wise Withdrawals
        for withdrawal in wise_withdrawals:
            date_str, time_str = format_datetime(withdrawal.timestamp)
            ref = f"WS-{user.id}-{withdrawal.pk}-{str(user.account_no)[-4:]}"
            data.append([
                ref,
                "Debit",
                "Wise Withdrawal",
                f"{user.account.account_currency} {withdrawal.amount}",
                date_str,
                time_str,
                f"Wise: {withdrawal.wise_email}",
                withdrawal.status
            ])

        # Create the table with enhanced styling
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#4CAF50'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#FFFFFF'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
            ('BACKGROUND', (0, 1), (-1, -1), '#F1F1F1'),
            ('TEXTCOLOR', (0, 1), (-1, -1), '#000000'),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ['#FFFFFF', '#F9F9F9']),
            ('GRID', (0, 0), (-1, -1), 1, '#DDDDDD'),
        ]))

        elements.append(table)
        doc.build(elements)

        # Get the value of the BytesIO buffer and add it to the response
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response

    return render(request, 'transactions/history.html', context)


# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import MailSubscription
import json

@require_POST
def subscribe_newsletter(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)

        # Check if email already exists
        if MailSubscription.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already subscribed to our newsletter.'
            }, status=400)

        # Create new subscription
        MailSubscription.objects.create(email=email)
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for subscribing to our newsletter!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        }, status=500)


def check_deposit(request):
    if request.method == 'POST':
        form = CheckDepositForm(request.POST, request.FILES)
        if form.is_valid():
            check_deposit = form.save(commit=False)
            check_deposit.user = request.user
            check_deposit.save()
            amount = check_deposit.amount

            messages.success(request, f"Check deposit of ${amount:.2f} successfully submitted! You will receive a notification about the transaction details.")
            return redirect('home')
    else:
        form = CheckDepositForm()
    return render(request, 'transactions/check_deposit.html', {'form': form})

