from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'HemoHub'
admin.site.site_title = 'HemoHub'
admin.site.index_title = 'Administração'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('paginas.urls')),
    path('contas/', include('usuarios.urls')),
    path('hemocentros/', include('hemocentros.urls')),
    path('doadores/', include('doadores.urls')),
    path('necessidades/', include('necessidades.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
