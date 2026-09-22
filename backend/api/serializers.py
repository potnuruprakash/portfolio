"""
Serializers for validating incoming portfolio CMS payloads.
"""
from rest_framework import serializers


class ProfileSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=200, required=True)
    professionalTitle = serializers.CharField(max_length=200, required=True)
    typingTitles = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    shortIntroduction = serializers.CharField(max_length=500, required=False, allow_blank=True)
    about = serializers.CharField(max_length=5000, required=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    profileImage = serializers.CharField(max_length=500, required=False, allow_blank=True)
    availability = serializers.CharField(max_length=200, required=False, allow_blank=True)
    careerGoal = serializers.CharField(max_length=300, required=False, allow_blank=True)
    interests = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    published = serializers.BooleanField(required=False, default=True)


class EducationSerializer(serializers.Serializer):
    degree = serializers.CharField(max_length=255, required=True)
    institution = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    startDate = serializers.CharField(max_length=50, required=True)
    endDate = serializers.CharField(max_length=50, required=True)
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    grade = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    displayOrder = serializers.IntegerField(required=False, default=0)
    visible = serializers.BooleanField(required=False, default=True)


class SkillSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    category = serializers.CharField(max_length=100, required=True)
    icon = serializers.CharField(max_length=100, required=False, allow_blank=True)
    proficiency = serializers.IntegerField(min_value=0, max_value=100, required=False, default=80)
    displayOrder = serializers.IntegerField(required=False, default=0)
    featured = serializers.BooleanField(required=False, default=False)
    visible = serializers.BooleanField(required=False, default=True)


class ProjectSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    slug = serializers.SlugField(max_length=255, required=False, allow_blank=True)
    shortDescription = serializers.CharField(max_length=500, required=True)
    detailedDescription = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    techStack = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True, default="General")
    githubUrl = serializers.URLField(required=False, allow_blank=True)
    liveUrl = serializers.CharField(max_length=500, required=False, allow_blank=True)
    image = serializers.CharField(max_length=500, required=False, allow_blank=True)
    featured = serializers.BooleanField(required=False, default=False)
    status = serializers.CharField(max_length=50, required=False, default="Completed")
    displayOrder = serializers.IntegerField(required=False, default=0)
    visible = serializers.BooleanField(required=False, default=True)
    published = serializers.BooleanField(required=False, default=True)


class ExperienceSerializer(serializers.Serializer):
    company = serializers.CharField(max_length=255, required=True)
    role = serializers.CharField(max_length=255, required=True)
    employmentType = serializers.CharField(max_length=100, required=False, default="Full-time")
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    startDate = serializers.CharField(max_length=50, required=True)
    endDate = serializers.CharField(max_length=50, required=False, allow_blank=True)
    currentlyWorking = serializers.BooleanField(required=False, default=False)
    description = serializers.CharField(max_length=3000, required=True)
    responsibilities = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    technologies = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    displayOrder = serializers.IntegerField(required=False, default=0)
    visible = serializers.BooleanField(required=False, default=True)


class CertificationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    issuer = serializers.CharField(max_length=255, required=True)
    issueDate = serializers.CharField(max_length=50, required=True)
    credentialId = serializers.CharField(max_length=200, required=False, allow_blank=True)
    verificationUrl = serializers.CharField(max_length=500, required=False, allow_blank=True)
    fileUrl = serializers.CharField(max_length=500, required=False, allow_blank=True)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    badgeText = serializers.CharField(max_length=50, required=False, allow_blank=True)
    badgeClass = serializers.CharField(max_length=50, required=False, allow_blank=True)
    displayOrder = serializers.IntegerField(required=False, default=0)
    visible = serializers.BooleanField(required=False, default=True)


class AchievementSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    type = serializers.CharField(max_length=100, required=True)  # hackathon, workshop, competition, leadership
    countDisplay = serializers.CharField(max_length=50, required=False, allow_blank=True)
    description = serializers.CharField(max_length=2000, required=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    displayOrder = serializers.IntegerField(required=False, default=0)
    visible = serializers.BooleanField(required=False, default=True)


class ResumeSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    filename = serializers.CharField(max_length=255, required=True)
    fileUrl = serializers.CharField(max_length=500, required=True)
    fileSize = serializers.IntegerField(required=False, default=0)
    isActive = serializers.BooleanField(required=False, default=False)
    displayOrder = serializers.IntegerField(required=False, default=0)


class SocialLinkSerializer(serializers.Serializer):
    platform = serializers.CharField(max_length=100, required=True)
    url = serializers.URLField(required=True)
    icon = serializers.CharField(max_length=100, required=False, allow_blank=True)
    displayOrder = serializers.IntegerField(required=False, default=0)
    visible = serializers.BooleanField(required=False, default=True)


class SiteSettingsSerializer(serializers.Serializer):
    portfolioTitle = serializers.CharField(max_length=255, required=True)
    seoTitle = serializers.CharField(max_length=255, required=True)
    seoDescription = serializers.CharField(max_length=1000, required=True)
    seoKeywords = serializers.CharField(max_length=500, required=False, allow_blank=True)
    faviconUrl = serializers.CharField(max_length=500, required=False, allow_blank=True)
    ogTitle = serializers.CharField(max_length=255, required=False, allow_blank=True)
    ogDescription = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    ogImage = serializers.CharField(max_length=500, required=False, allow_blank=True)
    contactEmail = serializers.EmailField(required=True)
    canonicalUrl = serializers.URLField(required=False, allow_blank=True)
    theme = serializers.CharField(max_length=50, required=False, default="dark")


class ReorderItemSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    displayOrder = serializers.IntegerField(required=True)


class ReorderSerializer(serializers.Serializer):
    items = serializers.ListField(child=ReorderItemSerializer(), required=True)
