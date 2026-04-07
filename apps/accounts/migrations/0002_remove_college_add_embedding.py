# Generated manually — removes college FK from User and adds AI embedding fields to Profile

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        # Task 1: Remove college FK from User
        migrations.RemoveField(
            model_name="user",
            name="college",
        ),
        # Task 3: Add AI embedding fields to Profile
        migrations.AddField(
            model_name="profile",
            name="skill_embedding",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="embedding_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
