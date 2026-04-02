from django.db import models
from django.conf import settings


class Scholarship(models.Model):

    class ScholarshipType(models.TextChoices):
        MERIT   = 'merit',   'Merit-based'
        NEED    = 'need',    'Need-based'
        SPORT   = 'sport',   'Sports'
        RESEARCH= 'research','Research'
        OTHER   = 'other',   'Other'

    posted_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_scholarships'
    )
    title        = models.CharField(max_length=200)
    provider     = models.CharField(max_length=200)
    amount       = models.CharField(max_length=100, blank=True, help_text='e.g. ₹50,000 or Full tuition')
    scholarship_type = models.CharField(max_length=20, choices=ScholarshipType.choices, default=ScholarshipType.MERIT)
    description  = models.TextField()
    eligibility  = models.TextField(blank=True)
    apply_link   = models.URLField(blank=True)
    deadline     = models.DateField(null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title