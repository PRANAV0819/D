# Converts User.department from ForeignKey(Department) to CharField with predefined choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_remove_college_add_embedding"),
    ]

    operations = [
        # Remove the old FK field
        migrations.RemoveField(
            model_name="user",
            name="department",
        ),
        # Add the new CharField with department choices
        migrations.AddField(
            model_name="user",
            name="department",
            field=models.CharField(
                max_length=20,
                blank=True,
                default='',
                choices=[
                    ('',      '— Select department —'),
                    ('AI_DS', 'AI & DS (Artificial Intelligence & Data Science)'),
                    ('CS',    'CS (Computer Science)'),
                    ('IT',    'IT (Information Technology)'),
                    ('ENTC',  'ENTC (Electronics & Telecommunication)'),
                    ('MECH',  'Mechanical Engineering'),
                    ('ELEC',  'Electrical Engineering'),
                ],
            ),
        ),
    ]
