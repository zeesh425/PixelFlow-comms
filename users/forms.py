from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser, Department, UserRegistrationRequest


class UserRegistrationRequestForm(forms.ModelForm):
    """Form for users to submit registration requests"""
    
    class Meta:
        model = UserRegistrationRequest
        fields = ['first_name', 'last_name', 'username', 'email', 'department', 'whatsapp_number']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your last name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your WhatsApp number (e.g., +923001234567)'
            })
        }
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Check if username already exists in CustomUser
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        
        # Check if username already exists in pending requests
        if UserRegistrationRequest.objects.filter(username=username, status='pending').exists():
            raise forms.ValidationError("A registration request with this username is already pending.")
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Check if email already exists in CustomUser
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        
        # Check if email already exists in pending requests
        if UserRegistrationRequest.objects.filter(email=email, status='pending').exists():
            raise forms.ValidationError("A registration request with this email is already pending.")
        
        return email
    
    def clean_whatsapp_number(self):
        whatsapp = self.cleaned_data.get('whatsapp_number')
        
        # Basic validation for WhatsApp number format
        if whatsapp and not whatsapp.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError("Please enter a valid WhatsApp number.")
        
        return whatsapp


class CodeVerificationForm(forms.Form):
    """Form for users to verify their one-time code and set password"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    
    one_time_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit code'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data
    
    def clean_one_time_code(self):
        code = self.cleaned_data.get('one_time_code')
        
        if code and not code.isdigit():
            raise forms.ValidationError("Code must be 6 digits.")
        
        if code and len(code) != 6:
            raise forms.ValidationError("Code must be exactly 6 digits.")
        
        return code


class CustomLoginForm(forms.Form):
    """Custom login form"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    def clean(self):
        
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            
            # ✅ Allow superuser or admin role to bypass approval
            if not user.is_approved and not user.is_superuser and not user.is_admin():
                raise forms.ValidationError("Your account is not approved yet. Please contact admin.")
            
            if not user.is_active:
                raise forms.ValidationError("Your account is disabled. Please contact admin.")
        
        return cleaned_data


class AdminApprovalForm(forms.ModelForm):
    """Form for admin to approve/reject registration requests"""
    
    class Meta:
        model = UserRegistrationRequest
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes...'
            })
        }