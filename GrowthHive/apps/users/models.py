"""
GrowthHive — apps/users/models.py

Three-model design:
  User     → extends AbstractUser; email-primary auth; role enum
  Profile  → OneToOne with User; extended personal/social fields
  Activity → OneToOne with User; denormalized counters for fast reads
             (updated via signals from other apps)

Why denormalized counters on Activity (not live aggregation)?
  Dashboard / profile pages hit activity stats on every load.
  COUNT(*) across 5 tables on every request does not scale.
  Counters are incremented atomically via F() expressions in signals —
  eventual consistency is acceptable for display-only stats.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


# ---------------------------------------------------------------------------
# Custom manager — email is the unique identifier, not username
# ---------------------------------------------------------------------------


class UserManager(BaseUserManager):
    """
    Manager that removes username from required fields and uses email
    as the canonical identifier for authentication.
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class User(AbstractUser, TimestampedModel):
    """
    Central auth model for GrowthHive.

    - Email replaces username as the login credential.
    - username is kept (AbstractUser requires it) but is NOT used for auth.
      It is auto-populated from the email local part on creation.
    - role drives permission logic across every app; change it only via
      admin or a dedicated role-change workflow (audit trail recommended).
    """

    class Role(models.TextChoices):
        STUDENT = "student", _("Student")
        ALUMNI = "alumni", _("Alumni")
        SENIOR = "senior", _("Senior")  # 3rd/4th year mentor-eligible
        ADMIN = "admin", _("Admin")

    # Override email to make it unique and required
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
    )

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )

    # Soft-delete instead of hard-delete — preserves referential integrity
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Use email for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are enough for createsuperuser

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["role", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"

    # ------------------------------------------------------------------
    # Role helpers — use these instead of raw string comparisons
    # ------------------------------------------------------------------

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_alumni(self) -> bool:
        return self.role == self.Role.ALUMNI

    @property
    def is_senior(self) -> bool:
        return self.role == self.Role.SENIOR

    @property
    def is_mentor_eligible(self) -> bool:
        """Alumni and seniors can accept mentorship requests."""
        return self.role in (self.Role.ALUMNI, self.Role.SENIOR)

    def get_full_name(self) -> str:
        full = super().get_full_name()
        return full if full.strip() else self.email.split("@")[0]

    def soft_delete(self) -> None:
        """Mark as deleted without removing from DB."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active", "updated_at"])


# ---------------------------------------------------------------------------
# Profile model
# ---------------------------------------------------------------------------


class Profile(TimestampedModel):
    """
    Extended user information — separated from User to keep auth model lean.

    Relationship: User 1 ← → 1 Profile  (auto-created via post_save signal)

    skills is stored as a PostgreSQL ArrayField of text — no join table
    overhead for a simple tag-like feature. A GIN index makes
    overlap/containment queries fast for the recommendation engine.

    For departments and years we use TextChoices so the frontend gets
    a stable enum contract without needing a separate DB table.
    """

    class Department(models.TextChoices):
        IT = "IT", _("Information Technology")
        CS = "CS", _("Computer Science")
        AIDS = "AIDS", _("AI & Data Science")
        ENTC = "ENTC", _("Electronics & Telecom")
        MECH = "MECH", _("Mechanical")
        CIVIL = "CIVIL", _("Civil")
        OTHER = "OTHER", _("Other")

    class Year(models.TextChoices):
        FE = "FE", _("First Year")
        SE = "SE", _("Second Year")
        TE = "TE", _("Third Year")
        BE = "BE", _("Fourth Year")
        ALUMNI = "ALUMNI", _("Alumni / Graduated")

    # ---- Core relation ----
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # ---- Personal info ----
    bio = models.TextField(blank=True, max_length=500)

    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
        help_text="Profile picture. Stored in S3 via django-storages.",
    )

    # ---- Academic info ----
    department = models.CharField(
        max_length=8,
        choices=Department.choices,
        blank=True,
    )

    year = models.CharField(
        max_length=8,
        choices=Year.choices,
        blank=True,
    )

    # ---- Skills ----
    # PostgreSQL ArrayField — requires psycopg2.
    # Fall back to JSONField if you ever need multi-DB support.
    skills = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="E.g. ['Python', 'React', 'Machine Learning']",
    )

    # ---- Social links ----
    github_link = models.URLField(blank=True)
    linkedin_link = models.URLField(blank=True)
    website_link = models.URLField(blank=True)

    # ---- Visibility ----
    is_public = models.BooleanField(
        default=True,
        help_text="When False, profile is only visible to the owner and admins.",
    )

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")
        indexes = [
            # GIN index on skills array for fast overlap queries used
            # by the mentor recommendation engine:
            #   Profile.objects.filter(skills__overlap=['Python', 'Django'])
            models.Index(
                fields=["skills"],
                name="profile_skills_gin",
                # Django 4.2+ supports opclasses directly on Index
                # For older versions use django.contrib.postgres.indexes.GinIndex
            ),
        ]

    def __str__(self) -> str:
        return f"Profile({self.user.email})"

    @property
    def avatar_url(self) -> str:
        """Safe fallback to a UI-Avatars service when no image is set."""
        if self.avatar:
            return self.avatar.url
        initials = self.user.get_full_name().replace(" ", "+") or "U"
        return f"https://ui-avatars.com/api/?name={initials}&background=random&size=256"

    def skill_list(self) -> list[str]:
        """Return skills sorted for consistent display."""
        return sorted(self.skills)

    def add_skill(self, skill: str) -> None:
        skill = skill.strip().title()
        if skill and skill not in self.skills:
            self.skills.append(skill)
            self.save(update_fields=["skills", "updated_at"])

    def remove_skill(self, skill: str) -> None:
        skill = skill.strip().title()
        if skill in self.skills:
            self.skills.remove(skill)
            self.save(update_fields=["skills", "updated_at"])


# ---------------------------------------------------------------------------
# Activity tracking model — GitHub-style contribution counters
# ---------------------------------------------------------------------------


class ActivityStats(TimestampedModel):
    """
    Denormalized activity counters for the profile dashboard.

    Design choice: single-row per user with integer counters.
    Each counter is incremented (never decremented naively) using
    F() expressions to avoid race conditions:

        ActivityStats.objects.filter(user=u).update(
            resources_uploaded=F('resources_uploaded') + 1
        )

    Other apps import and call the helper methods at the bottom
    of this file — keeping the update logic centralised here.

    A separate ActivityEvent model (for audit / heatmap) is kept minimal
    for now and can be expanded for a GitHub-style calendar heatmap later.
    """

    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="activity",
    )

    # ---- Per-module counters ----
    mentorship_requests_sent = models.PositiveIntegerField(default=0)
    mentorship_requests_received = models.PositiveIntegerField(default=0)
    mentorships_completed = models.PositiveIntegerField(default=0)

    projects_created = models.PositiveIntegerField(default=0)
    projects_joined = models.PositiveIntegerField(default=0)

    resources_uploaded = models.PositiveIntegerField(default=0)
    resources_downloads = models.PositiveIntegerField(
        default=0
    )  # others downloading YOUR resources

    opportunities_posted = models.PositiveIntegerField(default=0)
    opportunities_applied = models.PositiveIntegerField(default=0)

    listings_posted = models.PositiveIntegerField(default=0)
    items_sold = models.PositiveIntegerField(default=0)

    lost_found_reports = models.PositiveIntegerField(default=0)

    # ---- Streak / engagement ----
    last_active_at = models.DateTimeField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("activity stats")
        verbose_name_plural = _("activity stats")

    def __str__(self) -> str:
        return f"Activity({self.user.email})"

    @property
    def total_contributions(self) -> int:
        """Aggregate score shown on profile card."""
        return (
            self.mentorship_requests_sent
            + self.projects_created
            + self.projects_joined
            + self.resources_uploaded
            + self.opportunities_applied
            + self.listings_posted
            + self.lost_found_reports
        )


class ActivityEvent(TimestampedModel):
    """
    Lightweight event log — one row per meaningful user action.
    Supports a GitHub-style contribution heatmap on the profile page.

    Keep writes cheap: no FKs to other modules (just string slugs).
    Querying is always by user + date range; add a composite index.
    """

    class EventType(models.TextChoices):
        MENTORSHIP_REQUEST = "mentorship_request", _("Sent mentorship request")
        PROJECT_CREATED = "project_created", _("Created a project")
        PROJECT_JOINED = "project_joined", _("Joined a project")
        RESOURCE_UPLOAD = "resource_upload", _("Uploaded a resource")
        OPPORTUNITY_APPLY = "opportunity_apply", _("Applied to opportunity")
        LISTING_POSTED = "listing_posted", _("Posted a marketplace listing")
        LOST_FOUND_REPORT = "lost_found_report", _("Filed a lost/found report")
        LOGIN = "login", _("Logged in")

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    # Optional human-readable label (e.g. project title) for timeline display
    label = models.CharField(max_length=120, blank=True)
    # event_date mirrors created_at.date() — stored separately for fast
    # GROUP BY date queries (heatmap) without a CAST on a timestamptz column.
    event_date = models.DateField(db_index=True)

    class Meta:
        verbose_name = _("activity event")
        verbose_name_plural = _("activity events")
        indexes = [
            models.Index(fields=["user", "event_date"]),
            models.Index(fields=["user", "event_type"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.event_type} on {self.event_date}"


# ---------------------------------------------------------------------------
# Public helper — called by signals in other apps
# ---------------------------------------------------------------------------

from django.db.models import F
from django.utils import timezone


def record_activity(user: User, event_type: str, label: str = "") -> None:
    """
    Central entry point for recording an activity.

    Usage (from any other app's signal or service layer):

        from apps.users.models import record_activity, ActivityStats
        from apps.users.models import ActivityEvent

        # In mentorship/signals.py:
        record_activity(instance.student, ActivityEvent.EventType.MENTORSHIP_REQUEST)

    This function:
      1. Increments the matching counter on ActivityStats (atomic F())
      2. Appends a row to ActivityEvent for heatmap/timeline queries
      3. Updates last_active_at on ActivityStats
    """
    today = timezone.localdate()
    now = timezone.now()

    # Map event type → counter field name on ActivityStats
    COUNTER_MAP = {
        ActivityEvent.EventType.MENTORSHIP_REQUEST: "mentorship_requests_sent",
        ActivityEvent.EventType.PROJECT_CREATED: "projects_created",
        ActivityEvent.EventType.PROJECT_JOINED: "projects_joined",
        ActivityEvent.EventType.RESOURCE_UPLOAD: "resources_uploaded",
        ActivityEvent.EventType.OPPORTUNITY_APPLY: "opportunities_applied",
        ActivityEvent.EventType.LISTING_POSTED: "listings_posted",
        ActivityEvent.EventType.LOST_FOUND_REPORT: "lost_found_reports",
        ActivityEvent.EventType.LOGIN: "login_count",
    }

    field = COUNTER_MAP.get(event_type)
    if field:
        ActivityStats.objects.filter(user=user).update(
            **{field: F(field) + 1},
            last_active_at=now,
        )

    ActivityEvent.objects.create(
        user=user,
        event_type=event_type,
        label=label,
        event_date=today,
    )
