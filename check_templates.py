import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.template.loader import get_template
from django.template import TemplateDoesNotExist

# Full complete list of all templates referenced in all views
templates = [
    # projects
    'projects/list.html','projects/detail.html','projects/form.html','projects/my_projects.html',
    # scholarships  
    'scholarships/list.html','scholarships/detail.html','scholarships/form.html',
    # marketplace
    'marketplace/list.html','marketplace/detail.html','marketplace/form.html','marketplace/my_items.html',
    # lost_found
    'lost_found/list.html','lost_found/detail.html','lost_found/form.html',
    # resources
    'resources/list.html','resources/detail.html','resources/form.html',
    # events
    'events/list.html','events/detail.html','events/form.html',
]

for t in templates:
    try:
        get_template(t)
        print(f'OK   {t}')
    except TemplateDoesNotExist:
        print(f'MISS {t}')
    except Exception as e:
        print(f'ERR  {t}: {e}')
