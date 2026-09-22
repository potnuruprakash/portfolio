"""
Views for Portfolio CMS: Public APIs, Protected Admin CRUD APIs, Auth endpoints, and Dashboard.
"""
import json
import logging
from datetime import datetime
from bson import ObjectId
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from api.mongo import mongo_manager
from api.security import (
    IsAdminUserSession,
    check_login_rate_limit,
    record_failed_login,
    reset_login_attempts,
    log_audit_event,
)
from api.services.storage import FileStorageService
from api.serializers import (
    ProfileSerializer,
    EducationSerializer,
    SkillSerializer,
    ProjectSerializer,
    ExperienceSerializer,
    CertificationSerializer,
    AchievementSerializer,
    ResumeSerializer,
    SocialLinkSerializer,
    SiteSettingsSerializer,
    ReorderSerializer,
)

logger = logging.getLogger('api.views')


def serialize_doc(doc):
    """Convert MongoDB BSON document to clean JSON-serializable dict with 'id'."""
    if not doc:
        return None
    d = dict(doc)
    if '_id' in d:
        d['id'] = str(d.pop('_id'))
    return d


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        is_connected, _ = mongo_manager.check_connection()
        if is_connected:
            return Response({"status": "ok", "database": "connected"}, status=status.HTTP_200_OK)
        return Response({"status": "error", "database": "disconnected"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC READ-ONLY APIS
# ══════════════════════════════════════════════════════════════════════════════

class PublicProfileView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        doc = mongo_manager.profiles.find_one({"isDeleted": {"$ne": True}, "published": {"$ne": False}})
        if not doc:
            doc = mongo_manager.profiles.find_one({"isDeleted": {"$ne": True}})
        return Response({"success": True, "data": serialize_doc(doc) or {}})


class PublicEducationView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        cursor = mongo_manager.education.find({"isDeleted": {"$ne": True}, "visible": {"$ne": False}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})


class PublicSkillsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        cursor = mongo_manager.skills.find({"isDeleted": {"$ne": True}, "visible": {"$ne": False}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]

        # Group by category
        grouped = {}
        for skill in data:
            cat = skill.get("category", "Other")
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(skill)

        return Response({"success": True, "data": data, "grouped": grouped})


class PublicProjectsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        query = {"isDeleted": {"$ne": True}, "visible": {"$ne": False}, "published": {"$ne": False}}
        featured_param = request.GET.get('featured')
        if featured_param and featured_param.lower() in ('true', '1'):
            query["featured"] = True

        cursor = mongo_manager.projects.find(query).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})


class PublicExperienceView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        cursor = mongo_manager.experience.find({"isDeleted": {"$ne": True}, "visible": {"$ne": False}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})


class PublicCertificationsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        cursor = mongo_manager.certifications.find({"isDeleted": {"$ne": True}, "visible": {"$ne": False}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})


class PublicAchievementsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        cursor = mongo_manager.achievements.find({"isDeleted": {"$ne": True}, "visible": {"$ne": False}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})


class PublicResumeView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        doc = mongo_manager.resumes.find_one({"isDeleted": {"$ne": True}, "isActive": True})
        if not doc:
            doc = mongo_manager.resumes.find_one({"isDeleted": {"$ne": True}})
        return Response({"success": True, "data": serialize_doc(doc) or {}})


class PublicSocialLinksView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        cursor = mongo_manager.social_links.find({"isDeleted": {"$ne": True}, "visible": {"$ne": False}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})


class PublicSettingsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        doc = mongo_manager.site_settings.find_one({"key": "default_site_settings"})
        return Response({"success": True, "data": serialize_doc(doc) or {}})


class PublicStatsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """Dynamically calculated statistics for the portfolio."""
        published_projects = mongo_manager.projects.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}, "published": {"$ne": False}
        })
        visible_certifications = mongo_manager.certifications.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}
        })
        visible_skills = mongo_manager.skills.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}
        })
        hackathons_count = mongo_manager.achievements.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}, "type": {"$in": ["hackathon", "hackathons"]}
        })
        total_achievements = mongo_manager.achievements.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}
        })
        total_experience = mongo_manager.experience.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}
        })
        total_education = mongo_manager.education.count_documents({
            "isDeleted": {"$ne": True}, "visible": {"$ne": False}
        })

        return Response({
            "success": True,
            "data": {
                "projects": published_projects,
                "certifications": visible_certifications,
                "skills": visible_skills,
                "hackathons": hackathons_count,
                "achievements": total_achievements,
                "experience": total_experience,
                "education": total_education,
            }
        })


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN BASE CRUD HELPER
# ══════════════════════════════════════════════════════════════════════════════

def paginate_query(cursor, page: int = 1, page_size: int = 20):
    total = cursor.count_documents({}) if hasattr(cursor, 'count_documents') else None
    skip = (page - 1) * page_size
    items = list(cursor.skip(skip).limit(page_size))
    return [serialize_doc(i) for i in items]


# ══════════════════════════════════════════════════════════════════════════════
# PROTECTED ADMIN APIS
# ══════════════════════════════════════════════════════════════════════════════

class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUserSession]

    def get(self, request):
        stats = {
            "projects": mongo_manager.projects.count_documents({"isDeleted": {"$ne": True}}),
            "certifications": mongo_manager.certifications.count_documents({"isDeleted": {"$ne": True}}),
            "skills": mongo_manager.skills.count_documents({"isDeleted": {"$ne": True}}),
            "achievements": mongo_manager.achievements.count_documents({"isDeleted": {"$ne": True}}),
            "experience": mongo_manager.experience.count_documents({"isDeleted": {"$ne": True}}),
            "education": mongo_manager.education.count_documents({"isDeleted": {"$ne": True}}),
            "resumes": mongo_manager.resumes.count_documents({"isDeleted": {"$ne": True}}),
            "databaseStatus": "connected",
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
        }
        return Response({"success": True, "data": stats})


class AdminProfileView(APIView):
    permission_classes = [IsAdminUserSession]

    def get(self, request):
        doc = mongo_manager.profiles.find_one({"isDeleted": {"$ne": True}})
        return Response({"success": True, "data": serialize_doc(doc) or {}})

    def post(self, request):
        serializer = ProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data['slug'] = data.get('slug') or 'potnuru-prakash'
        data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
        data['isDeleted'] = False

        existing = mongo_manager.profiles.find_one({"slug": data['slug']})
        if existing:
            mongo_manager.profiles.update_one({"_id": existing['_id']}, {"$set": data})
            doc_id = str(existing['_id'])
            action = "UPDATE"
        else:
            data['createdAt'] = datetime.utcnow().isoformat() + "Z"
            ins = mongo_manager.profiles.insert_one(data)
            doc_id = str(ins.inserted_id)
            action = "CREATE"

        log_audit_event(action, "profiles", doc_id, changes=data, request=request)
        return Response({"success": True, "data": {"id": doc_id, **data}})

    def put(self, request):
        return self.post(request)


class GenericAdminCollectionListView(APIView):
    permission_classes = [IsAdminUserSession]
    collection_name = ""
    serializer_class = None

    def get_collection(self):
        return mongo_manager.get_collection(self.collection_name)

    def get(self, request):
        col = self.get_collection()
        query = {"isDeleted": {"$ne": True}}

        # Filtering
        if 'visible' in request.GET:
            query['visible'] = request.GET.get('visible').lower() in ('true', '1')
        if 'featured' in request.GET:
            query['featured'] = request.GET.get('featured').lower() in ('true', '1')
        if 'category' in request.GET:
            query['category'] = request.GET.get('category')

        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 50))))

        total = col.count_documents(query)
        cursor = col.find(query).sort("displayOrder", 1).skip((page - 1) * page_size).limit(page_size)
        items = [serialize_doc(d) for d in cursor]

        return Response({
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size if total else 1
            }
        })

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        now = datetime.utcnow().isoformat() + "Z"
        data['createdAt'] = now
        data['updatedAt'] = now
        data['isDeleted'] = False

        if 'title' in data and 'slug' in data and not data['slug']:
            data['slug'] = slugify(data['title'])

        col = self.get_collection()
        ins = col.insert_one(data)
        doc_id = str(ins.inserted_id)

        log_audit_event("CREATE", self.collection_name, doc_id, changes=data, request=request)
        return Response({"success": True, "data": serialize_doc(data)}, status=status.HTTP_201_CREATED)


class GenericAdminCollectionDetailView(APIView):
    permission_classes = [IsAdminUserSession]
    collection_name = ""
    serializer_class = None

    def get_collection(self):
        return mongo_manager.get_collection(self.collection_name)

    def get(self, request, pk):
        try:
            doc = self.get_collection().find_one({"_id": ObjectId(pk), "isDeleted": {"$ne": True}})
            if not doc:
                return Response({"success": False, "error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"success": True, "data": serialize_doc(doc)})
        except Exception:
            return Response({"success": False, "error": "Invalid document ID."}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        serializer = self.serializer_class(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            col = self.get_collection()
            existing = col.find_one({"_id": ObjectId(pk)})
            if not existing:
                return Response({"success": False, "error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

            data = serializer.validated_data
            data['updatedAt'] = datetime.utcnow().isoformat() + "Z"

            col.update_one({"_id": ObjectId(pk)}, {"$set": data})
            log_audit_event("UPDATE", self.collection_name, pk, changes=data, request=request)

            updated = col.find_one({"_id": ObjectId(pk)})
            return Response({"success": True, "data": serialize_doc(updated)})
        except Exception as ex:
            return Response({"success": False, "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            col = self.get_collection()
            existing = col.find_one({"_id": ObjectId(pk)})
            if not existing:
                return Response({"success": False, "error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

            col.update_one(
                {"_id": ObjectId(pk)},
                {"$set": {
                    "isDeleted": True,
                    "deletedAt": datetime.utcnow().isoformat() + "Z",
                    "deletedBy": request.user.username
                }}
            )
            log_audit_event("DELETE", self.collection_name, pk, request=request)
            return Response({"success": True, "message": "Record moved to trash (soft-deleted)."})
        except Exception as ex:
            return Response({"success": False, "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class GenericReorderView(APIView):
    permission_classes = [IsAdminUserSession]
    collection_name = ""

    def post(self, request):
        serializer = ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        col = mongo_manager.get_collection(self.collection_name)
        items = serializer.validated_data['items']

        for item in items:
            try:
                col.update_one(
                    {"_id": ObjectId(item['id'])},
                    {"$set": {"displayOrder": item['displayOrder'], "updatedAt": datetime.utcnow().isoformat() + "Z"}}
                )
            except Exception:
                pass

        log_audit_event("REORDER", self.collection_name, "batch", changes={"count": len(items)}, request=request)
        return Response({"success": True, "message": "Order updated successfully."})


# Concrete Collection Views
class AdminEducationListView(GenericAdminCollectionListView):
    collection_name = "education"
    serializer_class = EducationSerializer

class AdminEducationDetailView(GenericAdminCollectionDetailView):
    collection_name = "education"
    serializer_class = EducationSerializer

class AdminEducationReorderView(GenericReorderView):
    collection_name = "education"


class AdminSkillsListView(GenericAdminCollectionListView):
    collection_name = "skills"
    serializer_class = SkillSerializer

class AdminSkillsDetailView(GenericAdminCollectionDetailView):
    collection_name = "skills"
    serializer_class = SkillSerializer

class AdminSkillsReorderView(GenericReorderView):
    collection_name = "skills"


class AdminProjectsListView(GenericAdminCollectionListView):
    collection_name = "projects"
    serializer_class = ProjectSerializer

class AdminProjectsDetailView(GenericAdminCollectionDetailView):
    collection_name = "projects"
    serializer_class = ProjectSerializer

class AdminProjectsReorderView(GenericReorderView):
    collection_name = "projects"


class AdminExperienceListView(GenericAdminCollectionListView):
    collection_name = "experience"
    serializer_class = ExperienceSerializer

class AdminExperienceDetailView(GenericAdminCollectionDetailView):
    collection_name = "experience"
    serializer_class = ExperienceSerializer

class AdminExperienceReorderView(GenericReorderView):
    collection_name = "experience"


class AdminCertificationsListView(GenericAdminCollectionListView):
    collection_name = "certifications"
    serializer_class = CertificationSerializer

class AdminCertificationsDetailView(GenericAdminCollectionDetailView):
    collection_name = "certifications"
    serializer_class = CertificationSerializer

class AdminCertificationsReorderView(GenericReorderView):
    collection_name = "certifications"


class AdminAchievementsListView(GenericAdminCollectionListView):
    collection_name = "achievements"
    serializer_class = AchievementSerializer

class AdminAchievementsDetailView(GenericAdminCollectionDetailView):
    collection_name = "achievements"
    serializer_class = AchievementSerializer

class AdminAchievementsReorderView(GenericReorderView):
    collection_name = "achievements"


class AdminSocialLinksListView(GenericAdminCollectionListView):
    collection_name = "social_links"
    serializer_class = SocialLinkSerializer

class AdminSocialLinksDetailView(GenericAdminCollectionDetailView):
    collection_name = "social_links"
    serializer_class = SocialLinkSerializer

class AdminSocialLinksReorderView(GenericReorderView):
    collection_name = "social_links"


class AdminResumeListView(APIView):
    permission_classes = [IsAdminUserSession]

    def get(self, request):
        cursor = mongo_manager.resumes.find({"isDeleted": {"$ne": True}}).sort("displayOrder", 1)
        data = [serialize_doc(d) for d in cursor]
        return Response({"success": True, "data": data})

    def post(self, request):
        serializer = ResumeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data['createdAt'] = datetime.utcnow().isoformat() + "Z"
        data['updatedAt'] = data['createdAt']
        data['isDeleted'] = False

        if data.get('isActive'):
            mongo_manager.resumes.update_many({}, {"$set": {"isActive": False}})

        ins = mongo_manager.resumes.insert_one(data)
        doc_id = str(ins.inserted_id)
        log_audit_event("CREATE", "resumes", doc_id, changes=data, request=request)
        return Response({"success": True, "data": serialize_doc(data)}, status=status.HTTP_201_CREATED)


class AdminResumeSetActiveView(APIView):
    permission_classes = [IsAdminUserSession]

    def post(self, request, pk):
        try:
            target = mongo_manager.resumes.find_one({"_id": ObjectId(pk)})
            if not target:
                return Response({"success": False, "error": "Resume document not found."}, status=status.HTTP_404_NOT_FOUND)

            # Deactivate all others, activate target
            mongo_manager.resumes.update_many({}, {"$set": {"isActive": False}})
            mongo_manager.resumes.update_one({"_id": ObjectId(pk)}, {"$set": {"isActive": True, "updatedAt": datetime.utcnow().isoformat() + "Z"}})

            log_audit_event("ACTIVATE_RESUME", "resumes", pk, request=request)
            return Response({"success": True, "message": "Resume set to active."})
        except Exception as ex:
            return Response({"success": False, "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class AdminResumeDeleteView(APIView):
    permission_classes = [IsAdminUserSession]

    def delete(self, request, pk):
        try:
            mongo_manager.resumes.update_one(
                {"_id": ObjectId(pk)},
                {"$set": {"isDeleted": True, "deletedAt": datetime.utcnow().isoformat() + "Z"}}
            )
            log_audit_event("DELETE", "resumes", pk, request=request)
            return Response({"success": True, "message": "Resume deleted."})
        except Exception as ex:
            return Response({"success": False, "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class AdminSettingsView(APIView):
    permission_classes = [IsAdminUserSession]

    def get(self, request):
        doc = mongo_manager.site_settings.find_one({"key": "default_site_settings"})
        return Response({"success": True, "data": serialize_doc(doc) or {}})

    def put(self, request):
        serializer = SiteSettingsSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data['key'] = "default_site_settings"
        data['updatedAt'] = datetime.utcnow().isoformat() + "Z"

        mongo_manager.site_settings.update_one(
            {"key": "default_site_settings"},
            {"$set": data},
            upsert=True
        )
        log_audit_event("UPDATE", "site_settings", "default_site_settings", changes=data, request=request)
        return Response({"success": True, "data": data})


class AdminFileUploadView(APIView):
    permission_classes = [IsAdminUserSession]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"success": False, "error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        folder = request.POST.get('folder', 'uploads')

        try:
            result = FileStorageService.save_file(uploaded_file, request=request, folder=folder)
            return Response({"success": True, "data": result}, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({"success": False, "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class AdminAuditLogsView(APIView):
    permission_classes = [IsAdminUserSession]

    def get(self, request):
        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 20))))

        total = mongo_manager.audit_logs.count_documents({})
        cursor = mongo_manager.audit_logs.find({}).sort("timestamp", -1).skip((page - 1) * page_size).limit(page_size)
        items = [serialize_doc(d) for d in cursor]

        return Response({
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size if total else 1
            }
        })


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION & CMS DASHBOARD VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@ensure_csrf_cookie
def admin_login_view(request):
    """
    GET /manage/login/ - render dark-mode login form
    POST /manage/login/ - handle authentication with rate limiting
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('/manage/')

    context = {"error": None}

    if request.method == 'POST':
        # Rate limit check (max 5 failed attempts per 10 mins)
        allowed, wait_sec = check_login_rate_limit(request)
        if not allowed:
            context["error"] = "Too many failed login attempts. Please try again in 10 minutes."
            return render(request, 'admin/login.html', context, status=429)

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            reset_login_attempts(request)
            log_audit_event("LOGIN", "admins", str(user.id), admin_user=user.username, request=request)
            next_url = request.POST.get('next') or request.GET.get('next') or '/manage/'
            return redirect(next_url)
        else:
            record_failed_login(request)
            log_audit_event("FAILED_LOGIN", "admins", "unknown", changes={"attempted_username": username}, request=request)
            context["error"] = "Invalid username or password."

    return render(request, 'admin/login.html', context)


def admin_logout_view(request):
    """
    POST /manage/logout/ - terminate session and redirect to login
    """
    if request.user.is_authenticated:
        log_audit_event("LOGOUT", "admins", str(request.user.id), request=request)
        logout(request)
    return redirect('/manage/login/')


def admin_dashboard_view(request, section=None):
    """
    GET /manage/ - Render modern glassmorphic CMS dashboard
    Requires authentication; redirects unauthenticated visitors to /manage/login/.
    """
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return redirect(f"/manage/login/?next={request.path}")

    return render(request, 'admin/dashboard.html', {
        "admin_username": request.user.username,
        "admin_email": request.user.email,
        "active_section": section or "dashboard",
    })


def public_portfolio_view(request):
    """
    GET / - Serve public portfolio HTML
    """
    index_file = settings.BASE_DIR.parent / 'frontend' / 'index.html'
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html; charset=utf-8')
    return HttpResponse("Portfolio index.html not found.", status=404)
