"""
File storage service supporting safe uploads, validation, UUID naming, and local/cloud storage abstraction.
"""
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from rest_framework.exceptions import ValidationError
from api.mongo import mongo_manager
from api.security import log_audit_event

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/webp',
}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def validate_uploaded_file(file_obj: UploadedFile):
    """
    Validate extension, MIME type, and size.
    Raises ValidationError on invalid input.
    """
    if file_obj.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds the 15 MB limit ({file_obj.size / (1024*1024):.1f} MB uploaded).")

    ext = Path(file_obj.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    # Check MIME type
    mime_type = file_obj.content_type
    if not mime_type or mime_type == 'application/octet-stream':
        guessed, _ = mimetypes.guess_type(file_obj.name)
        mime_type = guessed or mime_type

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Unsupported MIME type '{mime_type}'.")


class FileStorageService:
    @staticmethod
    def save_file(file_obj: UploadedFile, request=None, folder: str = "uploads") -> Dict[str, Any]:
        """
        Validate, save file to storage with safe UUID filename, and save metadata to MongoDB.
        """
        validate_uploaded_file(file_obj)

        ext = Path(file_obj.name).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        now = datetime.utcnow()
        subfolder = f"{now.strftime('%Y%m')}"
        
        provider = getattr(settings, 'FILE_STORAGE_PROVIDER', 'local')

        if provider == 'local':
            upload_dir = Path(settings.MEDIA_ROOT) / folder / subfolder
            upload_dir.mkdir(parents=True, exist_ok=True)
            target_path = upload_dir / unique_name

            with open(target_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            file_url = f"{settings.MEDIA_URL}{folder}/{subfolder}/{unique_name}"
            storage_key = f"{folder}/{subfolder}/{unique_name}"
        else:
            # Extensible S3/R2 hook
            raise NotImplementedError("Cloud object storage provider configuration not yet initialized.")

        doc = {
            "originalName": file_obj.name,
            "storedName": unique_name,
            "mimeType": file_obj.content_type or 'application/octet-stream',
            "size": file_obj.size,
            "storageProvider": provider,
            "storageKey": storage_key,
            "url": file_url,
            "uploadedBy": request.user.username if request and request.user.is_authenticated else "admin",
            "createdAt": now.isoformat() + "Z",
            "isDeleted": False,
        }

        inserted = mongo_manager.files.insert_one(doc)
        doc.pop('_id', None)
        doc['id'] = str(inserted.inserted_id)

        log_audit_event(
            action="UPLOAD",
            collection_name="files",
            document_id=doc['id'],
            changes={"filename": unique_name, "size": file_obj.size},
            request=request
        )

        return doc

    @staticmethod
    def delete_file(file_id: str, request=None) -> bool:
        """
        Soft delete or remove file.
        """
        from bson import ObjectId
        try:
            doc = mongo_manager.files.find_one({"_id": ObjectId(file_id)})
            if not doc:
                return False

            if doc.get('storageProvider') == 'local':
                rel_path = doc.get('storageKey')
                if rel_path:
                    abs_path = Path(settings.MEDIA_ROOT) / rel_path
                    if abs_path.exists():
                        try:
                            abs_path.unlink()
                        except Exception:
                            pass

            mongo_manager.files.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"isDeleted": True, "deletedAt": datetime.utcnow().isoformat() + "Z"}}
            )
            log_audit_event(
                action="DELETE",
                collection_name="files",
                document_id=file_id,
                request=request
            )
            return True
        except Exception:
            return False
