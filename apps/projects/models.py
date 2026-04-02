from django.db import models
from django.conf import settings


class Project(models.Model):

    class Status(models.TextChoices):
        OPEN     = 'open',     'Open for members'
        ACTIVE   = 'active',   'Active'
        COMPLETED= 'completed','Completed'

    owner       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects'
    )
    title       = models.CharField(max_length=200)
    description = models.TextField()
    skills_needed = models.TextField(blank=True, help_text='Comma-separated skills')
    max_members = models.PositiveSmallIntegerField(default=5)
    github_url  = models.URLField(blank=True)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at  = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='ProjectMember', related_name='joined_projects'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def skills_list(self):
        return [s.strip() for s in self.skills_needed.split(',') if s.strip()]

    def member_count(self):
        return self.project_members.filter(is_approved=True).count()


class ProjectMember(models.Model):
    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_members')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role        = models.CharField(max_length=100, blank=True, help_text='e.g. Frontend Dev, Designer')
    is_approved = models.BooleanField(default=False)
    joined_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f'{self.user.email} in {self.project.title}'


class ProjectTask(models.Model):

    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH   = 'high',   'High'

    class TaskStatus(models.TextChoices):
        TODO  = 'todo',  'To Do'
        DOING = 'doing', 'In Progress'
        DONE  = 'done',  'Done'

    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title       = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_tasks'
    )
    priority    = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status      = models.CharField(max_length=10, choices=TaskStatus.choices, default=TaskStatus.TODO)
    due_date    = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status', '-priority']

    def __str__(self):
        return self.title