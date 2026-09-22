"""
Comprehensive automated tests for Portfolio CMS:
- Health check
- Authentication & Rate limiting
- Authorization enforcement on /manage and /api/admin/*
- Public APIs & Dynamic stats
- Admin CRUD mutations & soft delete
- File upload validation
- Public portfolio root view
"""
from io import BytesIO
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class HealthCheckTests(APITestCase):
    def test_health_check_connected(self):
        url = reverse('api:health-check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok", "database": "connected"})

    def test_health_check_disconnected(self):
        url = reverse('api:health-check')
        with patch('api.mongo.mongo_manager.check_connection', return_value=(False, "disconnected")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertEqual(response.data, {"status": "error", "database": "disconnected"})


class PublicApiTests(APITestCase):
    def test_public_profile(self):
        res = self.client.get(reverse('api:public-profile'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))

    def test_public_skills(self):
        res = self.client.get(reverse('api:public-skills'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))
        self.assertIn('grouped', res.data)

    def test_public_projects(self):
        res = self.client.get(reverse('api:public-projects'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))

        res_feat = self.client.get(reverse('api:public-projects') + "?featured=true")
        self.assertEqual(res_feat.status_code, status.HTTP_200_OK)

    def test_public_education(self):
        res = self.client.get(reverse('api:public-education'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))

    def test_public_certifications(self):
        res = self.client.get(reverse('api:public-certifications'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))

    def test_public_achievements(self):
        res = self.client.get(reverse('api:public-achievements'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))

    def test_public_resume(self):
        res = self.client.get(reverse('api:public-resume'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))

    def test_public_stats(self):
        res = self.client.get(reverse('api:public-stats'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))
        stats = res.data.get('data', {})
        self.assertIn('projects', stats)
        self.assertIn('certifications', stats)
        self.assertIn('skills', stats)


class AuthenticationAndSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.username = "test_cms_admin"
        self.password = "Secur3P@ssword2026!"
        self.admin = User.objects.create_superuser(
            username=self.username,
            email="testadmin@example.com",
            password=self.password
        )

    def test_unauthenticated_manage_redirects(self):
        client = Client()
        res = client.get('/manage/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/manage/login/', res.url)

    def test_unauthenticated_admin_api_rejected(self):
        client = Client()
        res = client.get('/api/admin/projects/')
        self.assertIn(res.status_code, (401, 403))

    def test_valid_login(self):
        client = Client()
        res = client.post('/manage/login/', {
            'username': self.username,
            'password': self.password,
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/manage/')

        # Now can access dashboard
        dash_res = client.get('/manage/')
        self.assertEqual(dash_res.status_code, 200)

    def test_invalid_login_generic_message(self):
        client = Client()
        res = client.post('/manage/login/', {
            'username': self.username,
            'password': 'WrongPassword123!',
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Invalid username or password.")

    def test_login_rate_limiting(self):
        client = Client()
        for _ in range(5):
            client.post('/manage/login/', {'username': 'test_admin', 'password': 'wrong'})
        # 6th attempt triggers 429 rate limit
        res = client.post('/manage/login/', {'username': 'test_admin', 'password': 'wrong'})
        self.assertEqual(res.status_code, 429)
        self.assertContains(res, "Too many failed login attempts", status_code=429)

    def test_logout_terminates_session(self):
        client = Client()
        client.login(username=self.username, password=self.password)
        res = client.post('/manage/logout/')
        self.assertEqual(res.status_code, 302)

        # After logout, accessing manage redirects to login
        res_manage = client.get('/manage/')
        self.assertEqual(res_manage.status_code, 302)
        self.assertIn('/manage/login/', res_manage.url)


class AdminCrudTests(TestCase):
    def setUp(self):
        self.username = "crud_admin"
        self.password = "Secur3P@ssword2026!"
        self.admin = User.objects.create_superuser(
            username=self.username,
            email="crud@example.com",
            password=self.password
        )
        self.client.login(username=self.username, password=self.password)

    def test_project_crud(self):
        # 1. Create project
        payload = {
            "title": "Test AI Project",
            "category": "AI / Cloud",
            "shortDescription": "Test short description for automated test.",
            "techStack": ["Python", "Django"],
            "featured": True,
            "published": True
        }
        create_res = self.client.post(
            reverse('api:admin-projects-list'),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(create_res.status_code, 201)
        proj_id = create_res.json()['data']['id']

        # 2. Update project
        update_res = self.client.put(
            reverse('api:admin-projects-detail', kwargs={'pk': proj_id}),
            data={"title": "Updated AI Project"},
            content_type='application/json'
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()['data']['title'], "Updated AI Project")

        # 3. Soft Delete project
        del_res = self.client.delete(
            reverse('api:admin-projects-detail', kwargs={'pk': proj_id})
        )
        self.assertEqual(del_res.status_code, 200)

    def test_reorder_endpoint(self):
        res = self.client.post(
            reverse('api:admin-projects-reorder'),
            data={"items": [{"id": "507f1f77bcf86cd799439011", "displayOrder": 5}]},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get('success'))


class FileUploadTests(TestCase):
    def setUp(self):
        self.username = "file_admin"
        self.password = "Secur3P@ssword2026!"
        self.admin = User.objects.create_superuser(
            username=self.username,
            email="fileadmin@example.com",
            password=self.password
        )
        self.client.login(username=self.username, password=self.password)

    def test_reject_executable_extension(self):
        exe_file = SimpleUploadedFile("malicious.exe", b"MZ executable binary content", content_type="application/x-msdownload")
        res = self.client.post(reverse('api:admin-file-upload'), {'file': exe_file})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json().get('success'))

    def test_valid_pdf_upload(self):
        pdf_file = SimpleUploadedFile("sample_cert.pdf", b"%PDF-1.4 sample pdf content", content_type="application/pdf")
        res = self.client.post(reverse('api:admin-file-upload'), {'file': pdf_file})
        self.assertEqual(res.status_code, 201)
        data = res.json().get('data', {})
        self.assertIn('.pdf', data.get('storedName', ''))
        self.assertTrue(data.get('url', '').startswith('/media/'))

    def test_valid_photo_upload_and_patch_profile(self):
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        photo_file = SimpleUploadedFile("avatar.png", png_content, content_type="image/png")
        upload_res = self.client.post(reverse('api:admin-file-upload'), {'file': photo_file, 'folder': 'profile'})
        self.assertEqual(upload_res.status_code, 201)
        photo_url = upload_res.json()['data']['url']
        self.assertTrue(photo_url.startswith('/media/profile/'))

        # PATCH /api/admin/profile/ to set profileImage
        patch_res = self.client.patch(
            reverse('api:admin-profile'),
            data={'profileImage': photo_url},
            content_type='application/json'
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()['data']['profileImage'], photo_url)

        # GET /api/profile/ public check
        pub_res = self.client.get(reverse('api:public-profile'))
        self.assertEqual(pub_res.status_code, 200)
        self.assertEqual(pub_res.json()['data']['profileImage'], photo_url)

    def test_upload_reject_text_extension(self):
        txt_file = SimpleUploadedFile("readme.txt", b"plain text", content_type="text/plain")
        res = self.client.post(reverse('api:admin-file-upload'), {'file': txt_file})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json().get('success'))


class PublicPortfolioHomepageTest(TestCase):
    def test_root_serves_portfolio_html(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Potnuru Prakash")
        self.assertContains(res, "intro-video")


import os
import sys
import subprocess
from django.conf import settings


class DeploymentSecurityTests(TestCase):
    def test_development_security_defaults(self):
        """Verify local development environment settings defaults."""
        self.assertFalse(settings.SECURE_SSL_REDIRECT)
        self.assertFalse(settings.SESSION_COOKIE_SECURE)
        self.assertFalse(settings.CSRF_COOKIE_SECURE)
        self.assertEqual(settings.SECURE_HSTS_SECONDS, 0)
        self.assertFalse(settings.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertFalse(settings.SECURE_HSTS_PRELOAD)

    def test_production_security_settings_and_deploy_check(self):
        """Verify production settings when DEBUG=False and that check --deploy succeeds."""
        env = os.environ.copy()
        env["DEBUG"] = "False"
        env["SECRET_KEY"] = "super-secure-production-secret-key-that-is-at-least-64-characters-long-and-random-12345"
        env["ALLOWED_HOSTS"] = "render-portfolio.onrender.com"
        env["CSRF_TRUSTED_ORIGINS"] = "https://render-portfolio.onrender.com"

        # Verify python manage.py check --deploy passes with 0 warnings
        proc = subprocess.run(
            [sys.executable, "manage.py", "check", "--deploy"],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 0, f"check --deploy failed:\n{proc.stderr}\n{proc.stdout}")
        self.assertIn("System check identified no issues", proc.stderr + proc.stdout)

        # Verify setting values in production environment
        code = (
            "from django.conf import settings; "
            "print(f'{settings.DEBUG},{settings.SECURE_SSL_REDIRECT},{settings.SESSION_COOKIE_SECURE},{settings.CSRF_COOKIE_SECURE},{settings.SECURE_HSTS_SECONDS}')"
        )
        proc_eval = subprocess.run(
            [sys.executable, "-c", code],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc_eval.returncode, 0)
        out = proc_eval.stdout.strip()
        self.assertEqual(out, "False,True,True,True,31536000")

    def test_production_refuses_missing_secret_key(self):
        """Verify production refuses to boot with missing SECRET_KEY."""
        env = os.environ.copy()
        env["DEBUG"] = "False"
        env["SECRET_KEY"] = ""

        proc = subprocess.run(
            [sys.executable, "-c", "import config.settings"],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ImproperlyConfigured", proc.stderr)
        self.assertIn("Production security configuration error", proc.stderr)

    def test_production_refuses_django_insecure_secret_key(self):
        """Verify production refuses to boot with django-insecure- SECRET_KEY."""
        env = os.environ.copy()
        env["DEBUG"] = "False"
        insecure_key = "django-insecure-unusable-weak-dev-key-12345678901234567890"
        env["SECRET_KEY"] = insecure_key

        proc = subprocess.run(
            [sys.executable, "-c", "import config.settings"],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ImproperlyConfigured", proc.stderr)
        self.assertIn("Production security configuration error", proc.stderr)
        # Ensure secret is not printed in output
        self.assertNotIn(insecure_key, proc.stderr)

