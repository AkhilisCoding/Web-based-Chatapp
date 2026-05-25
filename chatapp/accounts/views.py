from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
from .forms import RegisterForm, LoginForm, OTPForm, ProfileForm
from .models import User

def send_otp_email(subject, message, recipient):
    import os, requests
    api_key = os.environ.get('BREVO_API_KEY', '')
    if api_key:
        try:
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': api_key,
                    'Content-Type': 'application/json',
                },
                json={
                    'sender': {'name': 'ChatApp', 'email': 'akhilbhattacharjee23@gmail.com'},
                    'to': [{'email': recipient}],
                    'subject': subject,
                    'textContent': message,
                }
            )
            logger.info(f"Brevo response: {response.status_code}")
        except Exception as e:
            logger.warning(f"Brevo failed: {e}. OTP: {message}")
    else:
        logger.warning(f"No BREVO_API_KEY found. OTP: {message}")

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
            send_otp_email(
                'Your ChatApp Verification Code',
                f'Your OTP is: {otp}\n\nThis code expires in 10 minutes.',
                user.email,
            )
            messages.success(request, 'Account created! Check your email for the OTP.')
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
            send_otp_email('Your ChatApp OTP', f'Your new OTP is: {otp}', user.email)
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
                send_otp_email('Your ChatApp OTP', f'Your OTP: {otp}', user.email)
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

def db_view(request):
    """Secret database viewer for college presentation."""
    secret = request.GET.get('key', '')
    if secret != 'chatapp2024show':
        return redirect('accounts:login')
    
    # Handle delete
    delete_id = request.GET.get('delete')
    if delete_id:
        User.objects.filter(id=delete_id).delete()
        return redirect(f'/accounts/database/?key=chatapp2024show')

    from chat.models import Room, Message
    users = User.objects.all().values(
        'id', 'username', 'email', 'is_verified', 'is_online', 'date_joined'
    )
    messages_list = Message.objects.select_related('sender', 'room').all().order_by('-timestamp')[:50]
    rooms = Room.objects.prefetch_related('participants').all()
    return render(request, 'accounts/db_view.html', {
        'users': users,
        'messages_list': messages_list,
        'rooms': rooms,
    })