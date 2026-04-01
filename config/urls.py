from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/',       admin.site.urls),
    path('accounts/',    include('apps.accounts.urls',    namespace='accounts')),
    path('feed/',        include('apps.social.urls',      namespace='social')),
    path('connections/', include('apps.connections.urls', namespace='connections')),
    path('chat/',        include('apps.chat.urls',        namespace='chat')),    # ← add
    path('',             RedirectView.as_view(url='/feed/', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)