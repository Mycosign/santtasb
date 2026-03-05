
import datetime
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import User, AccountDetails, UserAddress
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)


class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100)
    age = forms.IntegerField(min_value=18)
    
    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "email",
            "password1",
            "password2",
            "contact_no",
            "age",
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow spaces in username
        self.fields['username'].validators = [validator for validator in self.fields['username'].validators 
                                             if not isinstance(validator, RegexValidator)]
        # Add a new validator that allows spaces
        self.fields['username'].validators.append(
            RegexValidator(
                regex=r'^[\w\s]+$',
                message='Username may contain letters, numbers, underscores, and spaces.',
                code='invalid_username'
            )
        )


class AccountDetailsForm(forms.ModelForm):
    class Meta:
        model = AccountDetails
        fields = [
            'picture'
        ]
        widgets = {
            'picture': forms.ClearableFileInput(),
        }




class UserAddressForm(forms.ModelForm):
    country = forms.CharField(
        label='Country',
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill shadow-sm border-primary',
            'placeholder': 'Enter your country',
            'style': 'max-width: 400px; margin-bottom: 15px;',
        })
    )

    class Meta:
        model = UserAddress
        fields = ['country']



class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your username',
                'required': True,
            }
        )
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your password',
                'required': True,
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['autocomplete'] = 'off'





class UserProfileEditForm(UserChangeForm):
    password = None  # Remove the password field from the form
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'contact_no']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AccountDetailsEditForm(forms.ModelForm):
    class Meta:
        model = AccountDetails
        fields = ['picture']
        widgets = {
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your old password was entered incorrectly. Please enter it again.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return cleaned_data


class ChangeEmailForm(forms.Form):
    new_email = forms.EmailField(label='New Email Address', required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if new_email == self.user.email:
            raise ValidationError("This is your current email address. Please enter a different one.")
        if User.objects.filter(email=new_email).exists():
            raise ValidationError("This email address is already in use. Please choose another one.")
        return new_email


