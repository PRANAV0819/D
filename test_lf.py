import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from apps.accounts.models import User
from apps.lost_found.views import item_detail
from apps.lost_found.models import Item

user = User.objects.filter(role='student').first()
if not user:
    print("No student user found")
else:
    item = Item.objects.first()
    if not item:
        print("No items found in db")
    else:
        factory = RequestFactory()
        request = factory.get(f'/lost-found/item/{item.id}/')
        request.user = user
        try:
            response = item_detail(request, pk=item.id)
            print("item_detail Status:", response.status_code)
            # Render response
            response.render()
        except Exception as e:
            import traceback
            traceback.print_exc()
