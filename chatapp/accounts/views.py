from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm, LoginForm, OTPForm, ProfileForm
from .models import User

def register_view(request):
    if request.user.is_authenticated:
        return redirect('chat:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False
            user.save()
            otp = user.generate_otp()
            request.session['otp_user_id'] = user.id
            # Send OTP via email
            send_mail(
                'Your ChatApp Verification Code',
                f'Your OTP is: {otp}\n\nThis code expires in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@chatapp.com',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, f'Account created! Check your email (or console) for the OTP.')
            return redirect('accounts:verify_otp')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('accounts:register')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('accounts:register')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if user.verify_otp(otp):
                user.is_verified = True
                user.otp_code = ''
                user.save()
                del request.session['otp_user_id']
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Email verified! Welcome to ChatApp.')
                return redirect('chat:home')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
    else:
        form = OTPForm()
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email})

def resend_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            otp = user.generate_otp()
            send_mail(
                'Your ChatApp Verification Code',
                f'Your new OTP is: {otp}',
                'noreply@chatapp.com',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'New OTP sent!')
        except User.DoesNotExist:
            pass
    return redirect('accounts:verify_otp')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_verified:
                request.session['otp_user_id'] = user.id
                otp = user.generate_otp()
                send_mail('Your ChatApp OTP', f'Your OTP: {otp}', 'noreply@chatapp.com', [user.email], fail_silently=False)
                messages.warning(request, 'Please verify your email first.')
                return redirect('accounts:verify_otp')
            login(request, user)
            return redirect('chat:home')
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})
