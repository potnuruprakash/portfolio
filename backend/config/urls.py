"""
Root URL configuration for portfolio project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from django.views.static import serve
from api import views

frontend_dir = settings.BASE_DIR.parent / 'frontend'
certificates_dir = settings.BASE_DIR.parent / 'Certificates'

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

    # ── Certificates Directory ──
    re_path(r'^Certificates/(?P<path>.*)$', serve, {'document_root': certificates_dir}),

    # ── Frontend Root Assets (styles.css, script.js, intro.mp4, profile.png, resume.pdf, etc.) ──
    re_path(
        r'^(?P<path>[^/]+\.(?:css|js|png|jpg|jpeg|svg|mp4|webm|pdf|ico|webp|woff|woff2|ttf|map))$',
        serve,
        {'document_root': frontend_dir}
    ),

    # ── Media Uploads Directory (uploads, photos, certificates) ──
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Static & Media fallbacks
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

