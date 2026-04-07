import random
import string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from .managers import UserManager


# ─────────────────────────────────────────────
# College & Department
# ─────────────────────────────────────────────

class College(models.Model):
    name   = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, unique=True)
    city   = models.CharField(max_length=100, blank=True)
    state  = models.CharField(max_length=100, blank=True)
    logo   = models.ImageField(upload_to='colleges/logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)

    class Meta:
        unique_together = ('college', 'code')
        ordering = ['name']

    def __str__(self):
        return f'{self.code} — {self.name}'


# ─────────────────────────────────────────────
# Custom User
# ─────────────────────────────────────────────

class User(AbstractUser):

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        ALUMNI  = 'alumni',  'Alumni'
        TEACHER = 'teacher', 'Teacher'

    username   = None
    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    # College field removed from signup — managed separately by admin if needed
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    is_email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f'{self.get_full_name()} <{self.email}>'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_alumni(self):
        return self.role == self.Role.ALUMNI

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER


# ─────────────────────────────────────────────
# Skill
# ─────────────────────────────────────────────

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    bio    = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)

    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    current_year    = models.PositiveSmallIntegerField(null=True, blank=True)

    github_url   = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    website      = models.URLField(blank=True)
    location     = models.CharField(max_length=100, blank=True)

    # ✅ FIXED: through model now uses Profile
    skills = models.ManyToManyField('Skill', through='UserSkill', blank=True)

    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    points      = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)

    is_open_to_work   = models.BooleanField(default=False)
    is_open_to_mentor = models.BooleanField(default=False)

    # ── AI Mentor Matching ────────────────────────────────────
    # Cached Gemini embedding vector for skill-based matching.
    # Stored as a JSON list of floats (768-dim). Recomputed
    # whenever skills are added or removed via signals.
    skill_embedding     = models.JSONField(null=True, blank=True)
    embedding_updated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile → {self.user.get_full_name()}'

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'


# ─────────────────────────────────────────────
# ✅ FIXED UserSkill (IMPORTANT)
# ─────────────────────────────────────────────

class UserSkill(models.Model):

    class Level(models.TextChoices):
        BEGINNER     = 'beginner',     'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED     = 'advanced',     'Advanced'
        EXPERT       = 'expert',       'Expert'

    # 🔥 FIX: use Profile instead of User
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='profile_skills')
    skill   = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level   = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)

    class Meta:
        unique_together = ('profile', 'skill')

    def __str__(self):
        return f'{self.profile.user.email} · {self.skill.name} ({self.level})'


# ─────────────────────────────────────────────
# OTP Verification
# ─────────────────────────────────────────────

class OTPVerification(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp        = models.CharField(max_length=6)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.conf import settings
        minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        return timezone.now() > self.created_at + timezone.timedelta(minutes=minutes)

    @classmethod
    def generate_for(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        otp_code = ''.join(random.choices(string.digits, k=6))
        return cls.objects.create(user=user, otp=otp_code)

    def __str__(self):
        return f'OTP for {self.user.email} (used={self.is_used})'