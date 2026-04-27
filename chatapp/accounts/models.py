from django.contrib.auth.models import AbstractUser
from django.db import models
import random, string
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=300, blank=True)
    is_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp_code

    def verify_otp(self, code):
        if not self.otp_code or not self.otp_created_at:
            return False
        expiry = self.otp_created_at + timedelta(minutes=10)
        if timezone.now() > expiry:
            return False
        return self.otp_code == code

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return f"https://api.dicebear.com/7.x/initials/svg?seed={self.username}"

    def __str__(self):
        return self.email
