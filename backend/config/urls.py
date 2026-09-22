"""
Root URL configuration for portfolio project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from api import views

urlpatterns = [
    # ── Public Portfolio Homepage ──
    path('', views.public_portfolio_view, name='public-portfolio'),

    # ── Admin Authentication ──
    path('manage/login/', views.admin_login_view, name='admin-login'),
    path('manage/logout/', views.admin_logout_view, name='admin-logout'),

    # ── Admin CMS Dashboard ──
    path('manage/', views.admin_dashboard_view, name='admin-dashboard'),
    path('manage/<str:section>/', views.admin_dashboard_view, name='admin-dashboard-section'),

    # ── REST API ──
    path('api/', include('api.urls')),
]

# Serve media files in development and production fallback
if settings.DEBUG or True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
