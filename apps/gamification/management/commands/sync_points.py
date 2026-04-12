from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum, F
from apps.accounts.models import Profile, User
from apps.gamification.models import UserActivity

class Command(BaseCommand):
    help = 'Recalculates all user points based on the current POINTS_MAP and activity history.'

    def handle(self, *args, **options):
        self.stdout.write("Starting point synchronization...")
        
        with transaction.atomic():
            # 1. Update points_earned in all UserActivity records to match current POINTS_MAP
            self.stdout.write("Updating points_earned in UserActivity logs...")
            for action_code, point_value in UserActivity.POINTS_MAP.items():
                updated_count = UserActivity.objects.filter(action=action_code).update(points_earned=point_value)
                if updated_count > 0:
                    self.stdout.write(f"  - Updated {updated_count} records for action '{action_code}' to {point_value} pts.")

            # 2. Reset Profile points to zero
            self.stdout.write("Resetting all profile points...")
            Profile.objects.all().update(points=0)

            # 3. Sum points for each user and update their profile
            self.stdout.write("Aggregating points for all users...")
            activities = (
                UserActivity.objects.values('user_id')
                .annotate(total_points=Sum('points_earned'))
            )

            profiles_to_update = []
            for entry in activities:
                user_id = entry['user_id']
                total_points = entry['total_points']
                
                # We use filter().update() to avoid individual save() overhead, 
                # but for smaller counts we could use list of objects.
                Profile.objects.filter(user_id=user_id).update(points=total_points)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully synchronized points for {activities.count()} users."))
