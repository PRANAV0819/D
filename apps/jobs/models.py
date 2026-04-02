from django.db import models
from django.conf import settings


class Job(models.Model):

    class JobType(models.TextChoices):
        FULLTIME    = 'full_time',   'Full Time'
        PARTTIME    = 'part_time',   'Part Time'
        INTERNSHIP  = 'internship',  'Internship'
        FREELANCE   = 'freelance',   'Freelance'
        CONTRACT    = 'contract',    'Contract'

    class WorkMode(models.TextChoices):
        REMOTE  = 'remote',  'Remote'
        ONSITE  = 'onsite',  'On-site'
        HYBRID  = 'hybrid',  'Hybrid'

    class Status(models.TextChoices):
        OPEN   = 'open',   'Open'
        CLOSED = 'closed', 'Closed'

    posted_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs'
    )
    title        = models.CharField(max_length=200)
    company      = models.CharField(max_length=200)
    location     = models.CharField(max_length=200, blank=True)
    job_type     = models.CharField(max_length=20, choices=JobType.choices, default=JobType.INTERNSHIP)
    work_mode    = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.REMOTE)
    description  = models.TextField()
    requirements = models.TextField(blank=True)
    salary       = models.CharField(max_length=100, blank=True, help_text='e.g. ₹15,000/month or Unpaid')
    deadline     = models.DateField(null=True, blank=True)
    apply_link   = models.URLField(blank=True)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} at {self.company}'

    def application_count(self):
        return self.applications.count()


class JobApplication(models.Model):

    class AppStatus(models.TextChoices):
        APPLIED   = 'applied',   'Applied'
        REVIEWING = 'reviewing', 'Under Review'
        ACCEPTED  = 'accepted',  'Accepted'
        REJECTED  = 'rejected',  'Rejected'

    job        = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications'
    )
    cover_note = models.TextField(max_length=1000, blank=True)
    resume     = models.FileField(upload_to='job_resumes/', blank=True, null=True)
    status     = models.CharField(max_length=20, choices=AppStatus.choices, default=AppStatus.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f'{self.applicant.email} → {self.job.title}'