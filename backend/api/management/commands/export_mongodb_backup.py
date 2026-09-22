"""
Management command to safely export all MongoDB Atlas collections to a timestamped JSON backup.
Never modifies or deletes existing MongoDB data.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from bson import json_util
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError
from api.mongo import mongo_manager, PORTFOLIO_COLLECTIONS


class Command(BaseCommand):
    help = "Safely exports all portfolio MongoDB collections to a timestamped JSON backup."

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='',
            help='Optional custom directory to store backups (defaults to backend/backups/).'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Testing connection to MongoDB Atlas..."))

        is_connected, message = mongo_manager.check_connection()
        if not is_connected:
            raise CommandError(f"Failed to connect to MongoDB Atlas: {message}")

        db = mongo_manager.db
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_dir = options.get('output_dir')

        if custom_dir:
            backup_dir = Path(custom_dir) / f"backup_{timestamp}"
        else:
            backup_dir = settings.BASE_DIR / 'backups' / f"backup_{timestamp}"

        backup_dir.mkdir(parents=True, exist_ok=True)
        self.stdout.write(f"Backup target directory: {backup_dir}")

        total_collections = 0
        total_documents = 0
        manifest = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "database": db.name,
            "collections": {}
        }

        try:
            available_collections = db.list_collection_names()
            collections_to_backup = set(PORTFOLIO_COLLECTIONS).union(available_collections)

            for col_name in sorted(collections_to_backup):
                if col_name.startswith('system.'):
                    continue

                col = db[col_name]
                cursor = col.find({})
                docs = list(cursor)
                count = len(docs)

                file_path = backup_dir / f"{col_name}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_util.dumps(docs, indent=2))

                manifest["collections"][col_name] = count
                total_collections += 1
                total_documents += count
                self.stdout.write(f"  + Backed up '{col_name}': {count} documents -> {file_path.name}")

            # Write manifest.json
            with open(backup_dir / "manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)

            self.stdout.write(self.style.SUCCESS(
                f"\nBackup completed successfully! "
                f"Exported {total_documents} total documents across {total_collections} collections."
            ))
            self.stdout.write(self.style.SUCCESS(f"Manifest written to {backup_dir / 'manifest.json'}"))

        except PyMongoError as pe:
            raise CommandError(f"MongoDB export error: {type(pe).__name__}")
        except Exception as ex:
            raise CommandError(f"Unexpected backup error: {str(ex)}")
