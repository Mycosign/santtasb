
from django.contrib import admin

from .models import *
# Register your models here.
from django.utils.html import format_html

from django.db import models
import uuid
from bankingsystem.admin_actions import export_as_csv
# admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import LocalWithdrawal, PayPalWithdrawal, SkrillWithdrawal, RevolutWithdrawal, WiseWithdrawal

class BaseWithdrawalAdmin(admin.ModelAdmin):
    """Base admin class for all withdrawal types"""
    list_per_page = 50
    date_hierarchy = 'timestamp'
    list_filter = ['status', 'timestamp']
    readonly_fields = ['timestamp']
    
    def get_amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    get_amount_display.short_description = 'Amount'
    
    def get_status_display(self, obj):
        status_colors = {
            'pending': 'orange',
            'completed': 'green',
            'cancelled': 'red',
            'declined': 'darkred'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    get_status_display.short_description = 'Status'

@admin.register(LocalWithdrawal)
class LocalWithdrawalAdmin(BaseWithdrawalAdmin):
    list_display = [
        'timestamp', 
        'user', 
        'recipient_name',
        'recipient_account_number',
        'get_amount_display',
        'get_status_display'
    ]
    search_fields = [
        'user__email', 
        'user__username',
        'recipient_name',
        'recipient_account_number',
        'recipient_email'
    ]
    list_filter = BaseWithdrawalAdmin.list_filter + ['user']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'timestamp')
        }),
        ('Recipient Details', {
            'fields': ('recipient_name', 'recipient_email', 'recipient_account_number')
        }),
        ('Transaction Details', {
            'fields': ('amount', 'description', 'status')
        }),
    )

@admin.register(PayPalWithdrawal)
class PayPalWithdrawalAdmin(BaseWithdrawalAdmin):
    list_display = [
        'timestamp',
        'user',
        'paypal_email',
        'get_amount_display',
        'get_status_display'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'paypal_email'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'timestamp')
        }),
        ('PayPal Details', {
            'fields': ('paypal_email',)
        }),
        ('Transaction Details', {
            'fields': ('amount', 'description', 'status')
        }),
    )

@admin.register(SkrillWithdrawal)
class SkrillWithdrawalAdmin(BaseWithdrawalAdmin):
    list_display = [
        'timestamp',
        'user',
        'skrill_email',
        'get_amount_display',
        'get_status_display'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'skrill_email'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'timestamp')
        }),
        ('Skrill Details', {
            'fields': ('skrill_email',)
        }),
        ('Transaction Details', {
            'fields': ('amount', 'description', 'status')
        }),
    )

@admin.register(RevolutWithdrawal)
class RevolutWithdrawalAdmin(BaseWithdrawalAdmin):
    list_display = [
        'timestamp',
        'user',
        'revolut_email',
        'get_amount_display',
        'get_status_display'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'revolut_email'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'timestamp')
        }),
        ('Revolut Details', {
            'fields': ('revolut_email',)
        }),
        ('Transaction Details', {
            'fields': ('amount', 'description', 'status')
        }),
    )

@admin.register(WiseWithdrawal)
class WiseWithdrawalAdmin(BaseWithdrawalAdmin):
    list_display = [
        'timestamp',
        'user',
        'wise_email',
        'get_amount_display',
        'get_status_display'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'wise_email'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'timestamp')
        }),
        ('Wise Details', {
            'fields': ('wise_email',)
        }),
        ('Transaction Details', {
            'fields': ('amount', 'description', 'status')
        }),
    )

# Add custom admin site configurations
admin.site.site_header = 'Banking System Administration'
admin.site.site_title = 'Banking System Admin'
admin.site.index_title = 'Banking System Management'
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')
    list_filter = ('name', 'email')

admin.site.register(CONTACT_US, ContactUsAdmin)




class LoanDocumentInline(admin.TabularInline):
    model = LoanDocument
    extra = 0


class LoanPaymentInline(admin.TabularInline):
    model = LoanPayment
    extra = 0


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'applicant', 'loan_product', 'loan_amount', 'term', 'status',
        'created_at', 'approved_at', 'funded_at'
    )
    list_filter = ('status', 'loan_product', 'term', 'rate_type', 'created_at', 'approved_at', 'funded_at')
    search_fields = ('reference_number', 'applicant__username', 'applicant__email', 'co_applicant__username')
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'approved_at', 'funded_at')
    inlines = [LoanDocumentInline, LoanPaymentInline]
    ordering = ('-created_at',)

    fieldsets = (
        ("Applicant Info", {
            'fields': ('applicant', 'co_applicant')
        }),
        ("Loan Details", {
            'fields': ('reference_number', 'loan_product', 'loan_amount', 'term', 'rate_type', 'interest_rate', 'purpose', 'collateral_description')
        }),
        ("Financials", {
            'fields': ('annual_income', 'existing_debt')
        }),
        ("Status & Dates", {
            'fields': ('status', 'created_at', 'updated_at')
        }),
        ("Decision", {
            'fields': ('approved_amount', 'monthly_payment', 'decision_notes')
        }),
    )

"""
@admin.register(LoanDocument)
class LoanDocumentAdmin(admin.ModelAdmin):
    list_display = ('loan_application', 'document_type', 'document_file', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('loan_application__reference_number',)
    ordering = ('-uploaded_at',)
"""

@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'loan_application', 'payment_date', 'amount_due', 'amount_paid', 'status', 'payment_method', 'paid_at'
    )
    list_filter = ('status', 'payment_date', 'paid_at')
    search_fields = ('loan_application__reference_number', 'transaction_id')
    ordering = ('-payment_date',)



class PayBillsAdmin(admin.ModelAdmin):
    list_display = ['user', 'address1', 'city', 'state', 'zipcode', 'nickname', 'delivery_method', 'amount', 'get_date', 'status']
    list_filter = ['delivery_method', 'status']
    search_fields = ['user__username', 'address1', 'city', 'state', 'zipcode', 'nickname']
    ordering = ['-timestamp']
    actions = ['mark_as_paid', 'mark_as_cancelled']

    def get_date(self, obj):
        return f"{obj.year}-{obj.month:02d}-{obj.day:02d}"

    get_date.short_description = 'Date of Delivery'

    def mark_as_paid(self, request, queryset):
        rows_updated = queryset.update(status='completed')
        if rows_updated == 1:
            message_bit = "1 record was"
        else:
            message_bit = f"{rows_updated} records were"
        self.message_user(request, f"{message_bit} successfully marked as paid.")

    mark_as_paid.short_description = "Mark selected bills as paid"

    def mark_as_cancelled(self, request, queryset):
        rows_updated = queryset.update(status='cancelled')
        if rows_updated == 1:
            message_bit = "1 record was"
        else:
            message_bit = f"{rows_updated} records were"
        self.message_user(request, f"{message_bit} successfully marked as cancelled.")

    mark_as_cancelled.short_description = "Mark selected bills as cancelled"

admin.site.register(PayBills, PayBillsAdmin)

class CardDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_type', 'masked_card_number', 'expiry_month', 'expiry_year', 'card_owner', 'timestamp')
    search_fields = ('user__username', 'card_number', 'card_owner')
    list_filter = ('card_type', 'timestamp')

    def masked_card_number(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"

    masked_card_number.short_description = 'Card Number'

admin.site.register(CardDetail, CardDetailAdmin)

class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_email', 'amount', 'recipient_account', 'date', 'status', 'current_balance')
    list_filter = ('status', )
    search_fields = ('user__email', 'user__username')
    
    def client_name(self, obj):
        return obj.user.get_full_name()
    client_name.short_description = 'Client Name'
    
    def client_email(self, obj):
        return obj.user.email
    client_email.short_description = 'Client Email'
    
    def recipient_account(self, obj):
        return obj.target
    recipient_account.short_description = 'Recipient Account'
    
    def current_balance(self, obj):
        deposits = obj.user.deposits.aggregate(models.Sum('amount'))['amount__sum'] or 0
        withdrawals = obj.user.withdrawals.aggregate(models.Sum('amount'))['amount__sum'] or 0
        balance = deposits - withdrawals
        return balance
    current_balance.short_description = 'Current Balance'
    
admin.site.register(Withdrawal, WithdrawalAdmin)



"""
class CryptoWITHDRAWAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_method', 'amount', 'status', 'date')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__username', 'user__email')

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data and form.cleaned_data['status'] == 'COMPLETE':
            obj.update_balance()
        obj.save()

admin.site.register(CryptoWITHDRAW, CryptoWITHDRAWAdmin)

"""


class CRYPWALLETSAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Bitcoin', {
            'fields': ('bitcoin', 'bitcoin_qr_code_preview', 'bitcoin_qr_code'),
            'description': 'Enter and manage Bitcoin wallet details.'
        }),
        ('Ethereum', {
            'fields': ('ethereum', 'ethereum_qr_code_preview', 'ethereum_qr_code'),
            'description': 'Enter and manage Ethereum wallet details.'
        }),

        ('USDT ERC20', {
            'fields': ('usdt_erc20', 'usdt_erc20_qr_code_preview', 'usdt_erc20_qr_code'),
            'description': 'Enter and manage usdt_erc20 wallet details.'
        }),
        ('Tron', {
            'fields': ('tron', 'tron_qr_code_preview', 'tron_qr_code'),
            'description': 'Enter and manage Tron wallet details.'
        }),
    )
    
    readonly_fields = (
        'bitcoin_qr_code_preview',
        'ethereum_qr_code_preview',
        'usdt_erc20_qr_code_preview',
        'tron_qr_code_preview',
    )

    def bitcoin_qr_code_preview(self, obj):
        if obj.bitcoin_qr_code:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.bitcoin_qr_code.url)
        return "No QR Code"
    bitcoin_qr_code_preview.short_description = "Bitcoin QR Code"

    def ethereum_qr_code_preview(self, obj):
        if obj.ethereum_qr_code:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.ethereum_qr_code.url)
        return "No QR Code"
    ethereum_qr_code_preview.short_description = "Ethereum QR Code"



    def usdt_erc20_qr_code_preview(self, obj):
        if obj.usdt_erc20_qr_code:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.usdt_erc20_qr_code.url)
        return "No QR Code"
    usdt_erc20_qr_code_preview.short_description = "usdt_erc20 QR Code"

    def tron_qr_code_preview(self, obj):
        if obj.tron_qr_code:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.tron_qr_code.url)
        return "No QR Code"
    tron_qr_code_preview.short_description = "Tron QR Code"

admin.site.register(CRYPWALLETS, CRYPWALLETSAdmin)



@admin.register(MailSubscription)
class MailSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_subscribed')
    search_fields = ('email',)
    list_filter = ('date_subscribed',)


@admin.register(BankTransfer)

class BankTransferAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Payment Method Details', {
            'fields': ('method', 'name_tag'),
            'description': 'Specify the payment method and its associated identifier.'
        }),
        ('QR Code Image', {
            'fields': ('qr_code_image_preview', 'qr_code_image'),
            'description': 'Upload or manage the QR code image for the payment method.'
        }),
        # 'Bank Image' section removed
    )

    readonly_fields = ('qr_code_image_preview', 'bank_image_preview')
    list_display = ('method', 'name_tag', 'qr_code_image_preview', 'bank_image_preview')
    search_fields = ('method', 'name_tag')
    list_filter = ('method',)

    def qr_code_image_preview(self, obj):
        if obj.qr_code_image:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.qr_code_image.url)
        return "No QR Code"
    qr_code_image_preview.short_description = "QR Code Preview"

    def bank_image_preview(self, obj):
        if obj.bank_image:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.bank_image.url)
        return "No Bank Image"
    bank_image_preview.short_description = "Bank Image Preview"
    


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_method', 'amount', 'status', 'date', 'timestamp')
    list_filter = ('status', 'payment_method', 'date')
    search_fields = ('user__username', 'payment_method', 'status', 'amount')
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    # Read-only fields
    readonly_fields = ('date', 'timestamp')

    fieldsets = (
        (None, {
            'fields': ('user', 'payment_method', 'amount', 'giftcard_type', 'giftcard_code', 'bank_transfer', 'status')
        }),
        ('Dates', {
            'fields': ('date', 'timestamp'),
            'classes': ('collapse',)  # Make this section collapsible
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Custom save logic (if needed)
        super().save_model(request, obj, form, change)

admin.site.register(Payment, PaymentAdmin)

admin.site.add_action(export_as_csv, name='export_selected')

admin.site.register(SUPPORT)


