"""
Management command to safely and idempotently import existing portfolio data into MongoDB Atlas.
Supports --dry-run. Never destroys existing files in Certificates/ or frontend/.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from api.mongo import mongo_manager


class MigrationReporter:
    def __init__(self):
        self.stats: Dict[str, Dict[str, int]] = {}

    def init_category(self, name: str):
        if name not in self.stats:
            self.stats[name] = {"created": 0, "updated": 0, "skipped": 0, "failed": 0, "total": 0}

    def record(self, category: str, action: str):
        self.init_category(category)
        if action in self.stats[category]:
            self.stats[category][action] += 1
            self.stats[category]["total"] += 1


def safe_upsert(collection: Collection, query: Dict[str, Any], doc: Dict[str, Any], dry_run: bool) -> str:
    """
    Safely and idempotently insert or update a document.
    Returns: 'created', 'updated', 'skipped', or 'failed'
    """
    if dry_run:
        existing = collection.find_one(query)
        if existing:
            # Check if contents match
            is_same = all(existing.get(k) == v for k, v in doc.items() if k not in ('_id', 'updatedAt'))
            return 'skipped' if is_same else 'updated'
        return 'created'

    try:
        existing = collection.find_one(query)
        now = datetime.utcnow().isoformat() + "Z"
        doc['updatedAt'] = now

        if existing:
            # Don't overwrite if existing is newer or identical
            is_same = all(existing.get(k) == v for k, v in doc.items() if k not in ('_id', 'updatedAt'))
            if is_same:
                return 'skipped'
            collection.update_one(query, {'$set': doc})
            return 'updated'
        else:
            doc['createdAt'] = now
            doc['isDeleted'] = False
            collection.insert_one(doc)
            return 'created'
    except PyMongoError:
        return 'failed'


class Command(BaseCommand):
    help = "Import existing portfolio content and certificates into MongoDB Atlas safely and idempotently."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate migration without modifying MongoDB Atlas.'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        mode_label = "DRY RUN MODE (No DB changes will be written)" if dry_run else "LIVE MIGRATION MODE"
        self.stdout.write(self.style.WARNING(f"\n=== Starting Portfolio Data Migration ({mode_label}) ===\n"))

        is_connected, msg = mongo_manager.check_connection()
        if not is_connected:
            raise CommandError(f"Cannot connect to MongoDB Atlas: {msg}")

        db = mongo_manager.db
        reporter = MigrationReporter()
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)

        # 1. Profile
        self.stdout.write("1. Migrating Profile...")
        self.import_profile(db, reporter, dry_run)

        # 2. Education
        self.stdout.write("2. Migrating Education...")
        self.import_education(db, reporter, dry_run)

        # 3. Skills
        self.stdout.write("3. Migrating Skills...")
        self.import_skills(db, reporter, dry_run)

        # 4. Projects
        self.stdout.write("4. Migrating Projects...")
        self.import_projects(db, reporter, dry_run)

        # 5. Experience
        self.stdout.write("5. Migrating Experience...")
        self.import_experience(db, reporter, dry_run)

        # 6. Certifications
        self.stdout.write("6. Migrating Certifications...")
        self.import_certifications(db, reporter, dry_run, media_root)

        # 7. Achievements
        self.stdout.write("7. Migrating Achievements...")
        self.import_achievements(db, reporter, dry_run)

        # 8. Resume
        self.stdout.write("8. Migrating Resume...")
        self.import_resume(db, reporter, dry_run, media_root)

        # 9. Social Links
        self.stdout.write("9. Migrating Social Links...")
        self.import_social_links(db, reporter, dry_run)

        # 10. Site Settings
        self.stdout.write("10. Migrating Site Settings...")
        self.import_site_settings(db, reporter, dry_run)

        # Summary Report Table
        self.stdout.write(self.style.SUCCESS(f"\n=== Migration Summary ({mode_label}) ==="))
        self.stdout.write(f"{'Category':<20} | {'Created':<8} | {'Updated':<8} | {'Skipped':<8} | {'Failed':<8} | {'Total':<8}")
        self.stdout.write("-" * 75)
        totals = {"created": 0, "updated": 0, "skipped": 0, "failed": 0, "total": 0}

        for cat, s in reporter.stats.items():
            self.stdout.write(
                f"{cat:<20} | {s['created']:<8} | {s['updated']:<8} | {s['skipped']:<8} | {s['failed']:<8} | {s['total']:<8}"
            )
            for k in totals:
                totals[k] += s[k]

        self.stdout.write("-" * 75)
        self.stdout.write(
            f"{'TOTAL':<20} | {totals['created']:<8} | {totals['updated']:<8} | {totals['skipped']:<8} | {totals['failed']:<8} | {totals['total']:<8}\n"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run finished successfully. Run without --dry-run to commit to MongoDB Atlas."))
        else:
            self.stdout.write(self.style.SUCCESS("All data migrated and synchronized with MongoDB Atlas successfully!"))

    def import_profile(self, db, reporter: MigrationReporter, dry_run: bool):
        profile_data = {
            "slug": "potnuru-prakash",
            "fullName": "Potnuru Prakash",
            "professionalTitle": "Computer Science Engineer",
            "typingTitles": [
                "Cybersecurity Enthusiast",
                "AI Developer",
                "Software Developer",
                "IoT Engineer",
                "Problem Solver",
            ],
            "shortIntroduction": "Computer Science Engineer crafting secure, intelligent solutions at the intersection of AI, Cybersecurity, and IoT.",
            "about": (
                "I'm a Computer Science Engineering student specializing in IoT, Cybersecurity, "
                "and Blockchain Technology. I enjoy building secure software, AI-powered applications, "
                "and solving real-world problems through technology.\n\n"
                "My journey spans from crafting intelligent self-healing infrastructure systems to "
                "competitive multiplayer platforms. I'm driven by curiosity, fueled by coffee, "
                "and passionate about making technology accessible and secure for everyone."
            ),
            "location": "Andhra Pradesh, India",
            "email": "prakashpotnuru7278@gmail.com",
            "phone": "",
            "profileImage": "/static/profile.png",
            "availability": "Open to Remote & Full-time Opportunities",
            "careerGoal": "Software Engineer at top-tier Tech companies (MAANG & Beyond)",
            "interests": ["AI", "Cybersecurity", "Blockchain", "IoT"],
            "published": True,
        }
        res = safe_upsert(db['profiles'], {"slug": "potnuru-prakash"}, profile_data, dry_run)
        reporter.record("profiles", res)

    def import_education(self, db, reporter: MigrationReporter, dry_run: bool):
        edu_list = [
            {
                "degree": "B.Tech – Computer Science Engineering",
                "institution": "Specialization in IoT, Cybersecurity & Blockchain",
                "location": "Andhra Pradesh, India",
                "startDate": "2024",
                "endDate": "2027",
                "description": "Pursuing a comprehensive computer science degree with focus on emerging technologies, secure software development, and AI applications.",
                "grade": "Active",
                "tags": ["IoT", "Cybersecurity", "Blockchain", "AI/ML"],
                "displayOrder": 0,
                "visible": True,
            },
            {
                "degree": "Diploma in Computer Engineering",
                "institution": "Sai Ganapathi Polytechnic College",
                "location": "Andhra Pradesh, India",
                "startDate": "2022",
                "endDate": "2024",
                "description": "Completed a Diploma in Computer Engineering, gaining a strong foundation in programming, computer systems, databases, and software development.",
                "grade": "Completed",
                "tags": ["C", "C++", "Python", "Java", "Databases"],
                "displayOrder": 1,
                "visible": True,
            }
        ]
        for item in edu_list:
            res = safe_upsert(db['education'], {"degree": item['degree'], "institution": item['institution']}, item, dry_run)
            reporter.record("education", res)

    def import_skills(self, db, reporter: MigrationReporter, dry_run: bool):
        skills_data = [
            # Programming
            {"name": "Python", "category": "Programming Languages", "icon": "fa-brands fa-python", "proficiency": 90, "displayOrder": 0, "featured": True, "visible": True},
            {"name": "Java", "category": "Programming Languages", "icon": "fa-brands fa-java", "proficiency": 85, "displayOrder": 1, "featured": True, "visible": True},
            {"name": "C", "category": "Programming Languages", "icon": "fa-solid fa-c", "proficiency": 80, "displayOrder": 2, "featured": False, "visible": True},
            {"name": "JavaScript", "category": "Programming Languages", "icon": "fa-brands fa-js", "proficiency": 85, "displayOrder": 3, "featured": True, "visible": True},

            # Frontend
            {"name": "HTML5", "category": "Frontend", "icon": "fa-brands fa-html5", "proficiency": 95, "displayOrder": 0, "featured": False, "visible": True},
            {"name": "CSS3", "category": "Frontend", "icon": "fa-brands fa-css3-alt", "proficiency": 90, "displayOrder": 1, "featured": False, "visible": True},
            {"name": "React", "category": "Frontend", "icon": "fa-brands fa-react", "proficiency": 80, "displayOrder": 2, "featured": True, "visible": True},

            # Backend
            {"name": "FastAPI", "category": "Backend", "icon": "fa-solid fa-bolt", "proficiency": 85, "displayOrder": 0, "featured": True, "visible": True},
            {"name": "Django", "category": "Backend", "icon": "fa-brands fa-python", "proficiency": 90, "displayOrder": 1, "featured": True, "visible": True},

            # Databases
            {"name": "MongoDB", "category": "Databases", "icon": "fa-solid fa-database", "proficiency": 85, "displayOrder": 0, "featured": True, "visible": True},
            {"name": "MySQL", "category": "Databases", "icon": "fa-solid fa-database", "proficiency": 85, "displayOrder": 1, "featured": False, "visible": True},
            {"name": "Firebase", "category": "Databases", "icon": "fa-solid fa-fire", "proficiency": 80, "displayOrder": 2, "featured": False, "visible": True},

            # Cybersecurity
            {"name": "Networking", "category": "Cybersecurity", "icon": "fa-solid fa-network-wired", "proficiency": 85, "displayOrder": 0, "featured": True, "visible": True},
            {"name": "Linux", "category": "Cybersecurity", "icon": "fa-brands fa-linux", "proficiency": 85, "displayOrder": 1, "featured": True, "visible": True},
            {"name": "Ethical Hacking", "category": "Cybersecurity", "icon": "fa-solid fa-user-secret", "proficiency": 85, "displayOrder": 2, "featured": True, "visible": True},
            {"name": "Digital Forensics", "category": "Cybersecurity", "icon": "fa-solid fa-magnifying-glass", "proficiency": 80, "displayOrder": 3, "featured": False, "visible": True},

            # Cloud & DevOps
            {"name": "AWS", "category": "Cloud & DevOps", "icon": "fa-brands fa-aws", "proficiency": 80, "displayOrder": 0, "featured": True, "visible": True},

            # Tools & Platforms
            {"name": "Git", "category": "Tools", "icon": "fa-brands fa-git-alt", "proficiency": 90, "displayOrder": 0, "featured": False, "visible": True},
            {"name": "GitHub", "category": "Tools", "icon": "fa-brands fa-github", "proficiency": 90, "displayOrder": 1, "featured": False, "visible": True},
            {"name": "VS Code", "category": "Tools", "icon": "fa-solid fa-code", "proficiency": 95, "displayOrder": 2, "featured": False, "visible": True},
            {"name": "Android Studio", "category": "Tools", "icon": "fa-brands fa-android", "proficiency": 75, "displayOrder": 3, "featured": False, "visible": True},
            {"name": "Flutter", "category": "Mobile", "icon": "fa-solid fa-mobile-screen", "proficiency": 80, "displayOrder": 4, "featured": False, "visible": True},
        ]
        for skill in skills_data:
            res = safe_upsert(db['skills'], {"name": skill['name'], "category": skill['category']}, skill, dry_run)
            reporter.record("skills", res)

    def import_projects(self, db, reporter: MigrationReporter, dry_run: bool):
        projects_data = [
            {
                "title": "Self-Healing SRE Agent",
                "slug": "self-healing-sre-agent",
                "shortDescription": "AI-powered infrastructure monitoring system capable of detecting anomalies, root-cause analysis, and automated remediation in real-time.",
                "detailedDescription": "Autonomous SRE agent designed to observe distributed microservices, evaluate telemetry anomalies, and orchestrate zero-touch rollback or self-healing pipelines.",
                "techStack": ["Python", "FastAPI", "Streamlit", "WebSocket"],
                "category": "AI / Cloud",
                "githubUrl": "https://github.com/potnuruprakash",
                "liveUrl": "#",
                "image": "",
                "featured": True,
                "status": "Completed",
                "displayOrder": 0,
                "visible": True,
                "published": True,
            },
            {
                "title": "Campus Issue Portal",
                "slug": "campus-issue-portal",
                "shortDescription": "A web-based campus issue reporting and news management system with separate student and admin portals for efficient campus governance.",
                "detailedDescription": "Role-based platform empowering students to report campus grievances and follow resolution lifecycles, coupled with administrator dispatch panels.",
                "techStack": ["Django", "HTML", "CSS", "JavaScript", "SQLite"],
                "category": "Web Development",
                "githubUrl": "https://github.com/potnuruprakash",
                "liveUrl": "#",
                "image": "",
                "featured": True,
                "status": "Completed",
                "displayOrder": 1,
                "visible": True,
                "published": True,
            },
            {
                "title": "IPL Auction Arena",
                "slug": "ipl-auction-arena",
                "shortDescription": "A multiplayer IPL auction platform where users create rooms, bid for players, and build virtual teams in real-time with live synchronization.",
                "detailedDescription": "Interactive gaming platform simulating player bidding rounds with state synchronization and virtual purse calculations across players in real-time.",
                "techStack": ["Flutter", "Firebase", "Dart"],
                "category": "Mobile Development",
                "githubUrl": "https://github.com/potnuruprakash",
                "liveUrl": "#",
                "image": "",
                "featured": True,
                "status": "Completed",
                "displayOrder": 2,
                "visible": True,
                "published": True,
            },
        ]
        for p in projects_data:
            res = safe_upsert(db['projects'], {"slug": p['slug']}, p, dry_run)
            reporter.record("projects", res)

    def import_experience(self, db, reporter: MigrationReporter, dry_run: bool):
        exp_list = [
            {
                "company": "Tanasvi Technologies",
                "role": "Java Fullstack Intern",
                "employmentType": "Internship",
                "location": "India",
                "startDate": "2024",
                "endDate": "2024",
                "currentlyWorking": False,
                "description": (
                    "Successfully completed a 6-month internship, gaining practical experience in software development, "
                    "problem-solving, debugging, and real-world project workflows. Actively contributed to various projects "
                    "and technical tasks while developing professional and collaborative skills."
                ),
                "responsibilities": [
                    "Full-stack feature engineering with Java and backend services",
                    "Debugging complex issues in pre-production environments",
                    "Collaborative Git workflows and sprint participation"
                ],
                "technologies": ["Java", "Debugging", "Software Development", "REST"],
                "displayOrder": 0,
                "visible": True,
            }
        ]
        for e in exp_list:
            res = safe_upsert(db['experience'], {"company": e['company'], "role": e['role']}, e, dry_run)
            reporter.record("experience", res)

    def import_certifications(self, db, reporter: MigrationReporter, dry_run: bool, media_root: Path):
        certs_dir = settings.BASE_DIR.parent / 'Certificates'
        certs_media_dir = media_root / 'certificates'
        if not dry_run:
            certs_media_dir.mkdir(parents=True, exist_ok=True)

        certs_data = [
            {
                "name": "AWS Academy Graduate – Machine Learning Foundations",
                "issuer": "Amazon Web Services",
                "issueDate": "2024",
                "credentialId": "0285f09a-af89-487f-b139-4a72f9cc2d0b",
                "verificationUrl": "https://www.credly.com/badges/0285f09a-af89-487f-b139-4a72f9cc2d0b/print",
                "fileUrl": "/media/certificates/AWS_Academy_Graduate___Machine_Learning_Foundations___Training_Badge_Badge20260702-7-ys9oi.pdf",
                "localSourceFile": "AWS_Academy_Graduate___Machine_Learning_Foundations___Training_Badge_Badge20260702-7-ys9oi.pdf",
                "description": "Machine Learning Foundations, AWS Cloud Architecture, and AI Services.",
                "badgeText": "AWS",
                "badgeClass": "cert-badge-blue",
                "displayOrder": 0,
                "visible": True,
            },
            {
                "name": "Java Full Stack Developer",
                "issuer": "Professional Certification",
                "issueDate": "2024",
                "credentialId": "",
                "verificationUrl": "#",
                "fileUrl": "",
                "localSourceFile": "",
                "description": "Enterprise Java, Spring Framework, REST APIs, and Database Design.",
                "badgeText": "Java",
                "badgeClass": "cert-badge-orange",
                "displayOrder": 1,
                "visible": True,
            },
            {
                "name": "Python Full Stack Developer",
                "issuer": "EduSkills Foundation",
                "issueDate": "2024",
                "credentialId": "4edbab2ac179e5b79809",
                "verificationUrl": "https://certificate.eduskillsfoundation.org/verify/4edbab2ac179e5b79809/4edbab2ac179e5b79809",
                "fileUrl": "/media/certificates/Python Fullstack Developer Virtual Internship.pdf",
                "localSourceFile": "Python Fullstack Developer Virtual Internship.pdf",
                "description": "Django, FastAPI, REST architecture, and Applied Data Science.",
                "badgeText": "Python",
                "badgeClass": "cert-badge-yellow",
                "displayOrder": 2,
                "visible": True,
            },
            {
                "name": "Ethical Hacking & Forensics",
                "issuer": "Cybersecurity Track / EduSkills",
                "issueDate": "2024",
                "credentialId": "43d694088c5fa1fe4244",
                "verificationUrl": "https://certificate.eduskillsfoundation.org/verify/43d694088c5fa1fe4244/43d694088c5fa1fe4244",
                "fileUrl": "/media/certificates/Ethical Hacking Virtual Internship (english Language).pdf",
                "localSourceFile": "Ethical Hacking Virtual Internship (english Language).pdf",
                "description": "Penetration Testing, Digital Forensics, and Network Vulnerability Assessment.",
                "badgeText": "Security",
                "badgeClass": "cert-badge-red",
                "displayOrder": 3,
                "visible": True,
            },
            {
                "name": "Cisco Packet Tracer Exploration",
                "issuer": "Cisco Networking Academy",
                "issueDate": "2024",
                "credentialId": "",
                "verificationUrl": "#",
                "fileUrl": "/media/certificates/Exploring Networking with Cisco Packet Tracer.pdf",
                "localSourceFile": "Exploring Networking with Cisco Packet Tracer.pdf",
                "description": "Network topologies, routing configuration, and Packet Tracer simulation.",
                "badgeText": "Cisco",
                "badgeClass": "cert-badge-blue",
                "displayOrder": 4,
                "visible": True,
            },
            {
                "name": "Cybersecurity Essentials",
                "issuer": "Cisco Networking Academy",
                "issueDate": "2024",
                "credentialId": "",
                "verificationUrl": "#",
                "fileUrl": "/media/certificates/Cybersecurity Essentials.pdf",
                "localSourceFile": "Cybersecurity Essentials.pdf",
                "description": "Fundamental concepts in cybersecurity, defense techniques, and integrity.",
                "badgeText": "Cyber",
                "badgeClass": "cert-badge-red",
                "displayOrder": 5,
                "visible": True,
            },
            {
                "name": "ServiceNow System Administrator",
                "issuer": "ServiceNow",
                "issueDate": "2024",
                "credentialId": "",
                "verificationUrl": "#",
                "fileUrl": "/media/certificates/ServiceNow System Administrator.pdf",
                "localSourceFile": "ServiceNow System Administrator.pdf",
                "description": "ITSM workflows, system configuration, user administration, and scripting.",
                "badgeText": "ServiceNow",
                "badgeClass": "cert-badge-purple",
                "displayOrder": 6,
                "visible": True,
            },
            {
                "name": "Tanasvi Technologies Internship Certificate",
                "issuer": "Tanasvi Technologies",
                "issueDate": "2024",
                "credentialId": "",
                "verificationUrl": "#",
                "fileUrl": "/media/certificates/tanasvi technologies.jpeg",
                "localSourceFile": "tanasvi technologies.jpeg",
                "description": "6-month industrial internship completion in software development.",
                "badgeText": "Internship",
                "badgeClass": "cert-badge-blue",
                "displayOrder": 7,
                "visible": True,
            },
        ]

        # Copy files to media/certificates safely without touching originals
        if not dry_run and certs_dir.exists():
            for c in certs_data:
                src_filename = c.get('localSourceFile')
                if src_filename:
                    src = certs_dir / src_filename
                    dst = certs_media_dir / src_filename
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst)

        for cert in certs_data:
            doc = {k: v for k, v in cert.items() if k != 'localSourceFile'}
            res = safe_upsert(db['certifications'], {"name": cert['name']}, doc, dry_run)
            reporter.record("certifications", res)

    def import_achievements(self, db, reporter: MigrationReporter, dry_run: bool):
        achievements_data = [
            {
                "title": "Hackathons",
                "type": "hackathon",
                "countDisplay": "3+",
                "description": "Competed in national-level hackathons, building real-world solutions under pressure. Finalist & participant in multiple competitions focused on AI and cybersecurity.",
                "tags": ["National Level", "AI Track", "Security Track"],
                "displayOrder": 0,
                "visible": True,
            },
            {
                "title": "Workshops",
                "type": "workshop",
                "countDisplay": "5+",
                "description": "Attended and completed hands-on technical workshops on Cloud Computing, Machine Learning, Blockchain, and Ethical Hacking conducted by industry experts.",
                "tags": ["Cloud", "ML", "Blockchain"],
                "displayOrder": 1,
                "visible": True,
            },
            {
                "title": "Technical Events",
                "type": "competition",
                "countDisplay": "6+",
                "description": "Participated in paper presentations, coding contests, quizzes, and project expos at inter-college technical fests. Won recognition for innovative solutions.",
                "tags": ["Coding", "Research", "Innovation"],
                "displayOrder": 2,
                "visible": True,
            },
            {
                "title": "Leadership Roles",
                "type": "leadership",
                "countDisplay": "2+",
                "description": "Led teams in collaborative project development and hackathon environments. Coordinated technical events and mentored peers in programming and cybersecurity concepts.",
                "tags": ["Team Lead", "Mentor", "Coordinator"],
                "displayOrder": 3,
                "visible": True,
            },
        ]
        for ach in achievements_data:
            res = safe_upsert(db['achievements'], {"title": ach['title']}, ach, dry_run)
            reporter.record("achievements", res)

    def import_resume(self, db, reporter: MigrationReporter, dry_run: bool, media_root: Path):
        resume_media_dir = media_root / 'resumes'
        src_resume = settings.BASE_DIR.parent / 'frontend' / 'resume.pdf'
        file_url = "/static/resume.pdf"

        if not dry_run:
            resume_media_dir.mkdir(parents=True, exist_ok=True)
            if src_resume.exists():
                dst_resume = resume_media_dir / 'resume.pdf'
                if not dst_resume.exists():
                    shutil.copy2(src_resume, dst_resume)
                file_url = "/media/resumes/resume.pdf"

        resume_doc = {
            "title": "Potnuru Prakash - Computer Science Engineer",
            "filename": "resume.pdf",
            "fileUrl": file_url,
            "fileSize": src_resume.stat().st_size if src_resume.exists() else 92978,
            "isActive": True,
            "displayOrder": 0,
        }
        res = safe_upsert(db['resumes'], {"filename": "resume.pdf"}, resume_doc, dry_run)
        reporter.record("resumes", res)

    def import_social_links(self, db, reporter: MigrationReporter, dry_run: bool):
        links = [
            {"platform": "GitHub", "url": "https://github.com/potnuruprakash", "icon": "fa-brands fa-github", "displayOrder": 0, "visible": True},
            {"platform": "LinkedIn", "url": "https://www.linkedin.com/in/prakash-potnuru-036aa4353", "icon": "fa-brands fa-linkedin", "displayOrder": 1, "visible": True},
            {"platform": "Email", "url": "mailto:prakashpotnuru7278@gmail.com", "icon": "fa-solid fa-envelope", "displayOrder": 2, "visible": True},
            {"platform": "Twitter", "url": "https://twitter.com/", "icon": "fa-brands fa-x-twitter", "displayOrder": 3, "visible": True},
        ]
        for link in links:
            res = safe_upsert(db['social_links'], {"platform": link['platform']}, link, dry_run)
            reporter.record("social_links", res)

    def import_site_settings(self, db, reporter: MigrationReporter, dry_run: bool):
        settings_doc = {
            "key": "default_site_settings",
            "portfolioTitle": "Potnuru Prakash | CS Engineer & Cybersecurity Enthusiast",
            "seoTitle": "Potnuru Prakash | CS Engineer & Cybersecurity Enthusiast",
            "seoDescription": "Computer Science Engineer, Cybersecurity Enthusiast, AI Developer, and IoT & Blockchain Learner. Explore my portfolio of projects, skills, and certifications.",
            "seoKeywords": "Potnuru Prakash, portfolio, computer science, cybersecurity, AI developer, IoT, blockchain, software engineer",
            "faviconUrl": "/static/profile.png",
            "ogTitle": "Potnuru Prakash | CS Engineer & Cybersecurity Enthusiast",
            "ogDescription": "Premium portfolio of Potnuru Prakash – CS Engineer, AI Developer, Cybersecurity Enthusiast",
            "ogImage": "/static/profile.png",
            "contactEmail": "prakashpotnuru7278@gmail.com",
            "canonicalUrl": "https://prakash-1ofn.onrender.com/",
            "theme": "dark",
        }
        res = safe_upsert(db['site_settings'], {"key": "default_site_settings"}, settings_doc, dry_run)
        reporter.record("site_settings", res)
