from django.db import models
from django.conf import settings


class ResourceCategory(models.TextChoices):
    NOTES       = 'notes',        'Notes'
    PREVIOUS_QP = 'previous_qp',  'Previous Question Papers'
    SYLLABUS    = 'syllabus',     'Syllabus'
    BOOK        = 'book',         'Book / Reference'
    OTHER       = 'other',        'Other'


class Resource(models.Model):
    uploaded_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resources'
    )
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    category     = models.CharField(max_length=30, choices=ResourceCategory.choices, default=ResourceCategory.NOTES)
    department   = models.CharField(
        max_length=20,
        choices=[('', '— Select department —')] + list(__import__('apps.accounts.models', fromlist=['DEPARTMENT_CHOICES']).DEPARTMENT_CHOICES)[1:],
        blank=True,
        default='',
    )
    subject      = models.CharField(max_length=200, blank=True)
    file         = models.FileField(upload_to='resources/')
    download_count = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title