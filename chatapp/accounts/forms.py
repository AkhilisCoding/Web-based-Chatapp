from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='form-control'),
            Field('email', css_class='form-control'),
            Field('password1', css_class='form-control'),
            Field('password2', css_class='form-control'),
            Submit('submit', 'Create Account', css_class='btn-primary w-100 mt-3'),
        )

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='form-control'),
            Field('password', css_class='form-control'),
            Submit('submit', 'Sign In', css_class='btn-primary w-100 mt-3'),
        )

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6, label='Verification Code',
                          widget=forms.TextInput(attrs={'placeholder': '000000', 'class': 'form-control text-center otp-input', 'maxlength': '6', 'autocomplete': 'off'}))

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
