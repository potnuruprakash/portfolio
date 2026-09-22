"""
URL Routing for Portfolio CMS API (Public and Admin).
"""
from django.urls import path
from api import views

app_name = 'api'

urlpatterns = [
    # ── Health Check ──
    path('health/', views.HealthCheckView.as_view(), name='health-check'),

    # ── Public Endpoints ──
    path('profile/', views.PublicProfileView.as_view(), name='public-profile'),
    path('education/', views.PublicEducationView.as_view(), name='public-education'),
    path('skills/', views.PublicSkillsView.as_view(), name='public-skills'),
    path('projects/', views.PublicProjectsView.as_view(), name='public-projects'),
    path('experience/', views.PublicExperienceView.as_view(), name='public-experience'),
    path('certifications/', views.PublicCertificationsView.as_view(), name='public-certifications'),
    path('achievements/', views.PublicAchievementsView.as_view(), name='public-achievements'),
    path('resume/', views.PublicResumeView.as_view(), name='public-resume'),
    path('social-links/', views.PublicSocialLinksView.as_view(), name='public-social-links'),
    path('settings/', views.PublicSettingsView.as_view(), name='public-settings'),
    path('stats/', views.PublicStatsView.as_view(), name='public-stats'),

    # ── Protected Admin Endpoints (/api/admin/...) ──
    path('admin/dashboard/stats/', views.AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('admin/profile/', views.AdminProfileView.as_view(), name='admin-profile'),

    # Education (reorder before <pk>)
    path('admin/education/', views.AdminEducationListView.as_view(), name='admin-education-list'),
    path('admin/education/reorder/', views.AdminEducationReorderView.as_view(), name='admin-education-reorder'),
    path('admin/education/<str:pk>/', views.AdminEducationDetailView.as_view(), name='admin-education-detail'),

    # Skills (reorder before <pk>)
    path('admin/skills/', views.AdminSkillsListView.as_view(), name='admin-skills-list'),
    path('admin/skills/reorder/', views.AdminSkillsReorderView.as_view(), name='admin-skills-reorder'),
    path('admin/skills/<str:pk>/', views.AdminSkillsDetailView.as_view(), name='admin-skills-detail'),

    # Projects (reorder before <pk>)
    path('admin/projects/', views.AdminProjectsListView.as_view(), name='admin-projects-list'),
    path('admin/projects/reorder/', views.AdminProjectsReorderView.as_view(), name='admin-projects-reorder'),
    path('admin/projects/<str:pk>/', views.AdminProjectsDetailView.as_view(), name='admin-projects-detail'),

    # Experience (reorder before <pk>)
    path('admin/experience/', views.AdminExperienceListView.as_view(), name='admin-experience-list'),
    path('admin/experience/reorder/', views.AdminExperienceReorderView.as_view(), name='admin-experience-reorder'),
    path('admin/experience/<str:pk>/', views.AdminExperienceDetailView.as_view(), name='admin-experience-detail'),

    # Certifications (reorder before <pk>)
    path('admin/certifications/', views.AdminCertificationsListView.as_view(), name='admin-certifications-list'),
    path('admin/certifications/reorder/', views.AdminCertificationsReorderView.as_view(), name='admin-certifications-reorder'),
    path('admin/certifications/<str:pk>/', views.AdminCertificationsDetailView.as_view(), name='admin-certifications-detail'),

    # Achievements (reorder before <pk>)
    path('admin/achievements/', views.AdminAchievementsListView.as_view(), name='admin-achievements-list'),
    path('admin/achievements/reorder/', views.AdminAchievementsReorderView.as_view(), name='admin-achievements-reorder'),
    path('admin/achievements/<str:pk>/', views.AdminAchievementsDetailView.as_view(), name='admin-achievements-detail'),

    # Resumes
    path('admin/resume/', views.AdminResumeListView.as_view(), name='admin-resume-list'),
    path('admin/resume/<str:pk>/set-active/', views.AdminResumeSetActiveView.as_view(), name='admin-resume-set-active'),
    path('admin/resume/<str:pk>/', views.AdminResumeDeleteView.as_view(), name='admin-resume-delete'),

    # Social Links (reorder before <pk>)
    path('admin/social-links/', views.AdminSocialLinksListView.as_view(), name='admin-social-links-list'),
    path('admin/social-links/reorder/', views.AdminSocialLinksReorderView.as_view(), name='admin-social-links-reorder'),
    path('admin/social-links/<str:pk>/', views.AdminSocialLinksDetailView.as_view(), name='admin-social-links-detail'),

    # Site Settings
    path('admin/settings/', views.AdminSettingsView.as_view(), name='admin-settings'),

    # File uploads
    path('admin/files/upload/', views.AdminFileUploadView.as_view(), name='admin-file-upload'),

    # Audit Logs
    path('admin/audit-logs/', views.AdminAuditLogsView.as_view(), name='admin-audit-logs'),
]
