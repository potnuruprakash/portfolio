"""
Management command to verify MongoDB Atlas connection and initialize collection schemas.
Does NOT insert fake user data.
"""
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError
from api.mongo import mongo_manager, PORTFOLIO_COLLECTIONS


class Command(BaseCommand):
    help = "Verifies MongoDB Atlas connection and ensures portfolio collections are initialized."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Testing connection to MongoDB Atlas..."))

        is_connected, message = mongo_manager.check_connection()
        if not is_connected:
            raise CommandError(
                f"Failed to connect to MongoDB Atlas ({message}). "
                "Please verify MONGODB_URI and MONGODB_DATABASE in backend/.env."
            )

        self.stdout.write(self.style.SUCCESS("Successfully connected to MongoDB Atlas!"))

        try:
            db = mongo_manager.db
            existing_collections = set(db.list_collection_names())
            self.stdout.write(f"Connected to database: '{db.name}'")

            created_count = 0
            for collection_name in PORTFOLIO_COLLECTIONS:
                if collection_name not in existing_collections:
                    db.create_collection(collection_name)
                    self.stdout.write(f"  + Created collection: {collection_name}")
                    created_count += 1
                else:
                    self.stdout.write(f"  - Collection already exists: {collection_name}")

            # Create basic indexes safely if collection is newly created or exists
            # admins: unique index on username
            db['admins'].create_index('username', unique=True, sparse=True)
            # profiles: unique index on slug
            db['profiles'].create_index('slug', unique=True, sparse=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nInitialization completed successfully! "
                    f"({created_count} collections created, {len(existing_collections)} existed previously)."
                )
            )
            self.stdout.write(self.style.SUCCESS("No dummy data inserted. Ready for CMS operations."))

        except PyMongoError as pe:
            raise CommandError(f"MongoDB operation failed: {type(pe).__name__}")
