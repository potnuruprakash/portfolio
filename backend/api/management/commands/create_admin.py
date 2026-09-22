"""
Management command to create or update a secure Django admin user.

Supports:
- Interactive local usage
- Non-interactive Render/production deployment
"""

import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


User = get_user_model()


class Command(BaseCommand):
    help = "Create or update a secure admin user for portfolio management."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Admin username",
        )

        parser.add_argument(
            "--email",
            type=str,
            help="Admin email",
        )

        parser.add_argument(
            "--password",
            type=str,
            help="Admin password",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE(
                "=== Portfolio CMS Admin Setup ==="
            )
        )

        username = options.get("username")
        email = options.get("email")
        password = options.get("password")

        # ============================================================
        # USERNAME
        # ============================================================

        if not username:
            username = input("Username: ").strip()

            if not username:
                raise CommandError("Username cannot be empty.")

        username = username.strip()

        # ============================================================
        # EMAIL
        # ============================================================

        if not email:
            # Only ask interactively when running locally
            email = input("Email: ").strip()

        email = email.strip()

        # ============================================================
        # PASSWORD
        # ============================================================

        if not password:
            while True:
                password_1 = getpass.getpass("Password: ")

                if not password_1:
                    self.stdout.write(
                        self.style.ERROR(
                            "Password cannot be empty."
                        )
                    )
                    continue

                password_2 = getpass.getpass(
                    "Confirm password: "
                )

                if password_1 != password_2:
                    self.stdout.write(
                        self.style.ERROR(
                            "Passwords do not match. Try again."
                        )
                    )
                    continue

                password = password_1
                break

        # ============================================================
        # PASSWORD VALIDATION
        # ============================================================

        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError(
                "Password validation failed: "
                + ", ".join(error.messages)
            )

        # ============================================================
        # FIND EXISTING USER
        # ============================================================

        user = User.objects.filter(
            username=username
        ).first()

        # ============================================================
        # CREATE USER
        # ============================================================

        if user is None:

            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin user '{username}' created successfully."
                )
            )

        # ============================================================
        # UPDATE EXISTING USER
        # ============================================================

        else:

            user.email = email
            user.set_password(password)

            user.is_active = True
            user.is_staff = True
            user.is_superuser = True

            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin user '{username}' updated successfully."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Admin authentication is ready."
            )
        )
