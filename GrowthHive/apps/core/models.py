"""
apps/core/models.py — Shared abstract base models for GrowthHive.

Every model in the project inherits from at least TimestampedModel
so we always have created_at / updated_at without repeating fields.
UUIDModel adds a UUID primary key — preferred for distributed systems
and avoids leaking sequential row counts to the API.
"""

import uuid

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base that adds created_at and updated_at to any model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base that replaces the default integer PK with a UUID."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
