"""
Management command to create a secure Django admin user interactively.
"""
import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Interactively create a secure admin user for portfolio management."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username (optional, for automation)')
        parser.add_argument('--email', type=str, help='Admin email (optional, for automation)')
        parser.add_argument('--password', type=str, help='Admin password (optional, for automation)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Create Portfolio CMS Admin User ==="))

        username = options.get('username')
        email = options.get('email')
        password = options.get('password')

        # Interactive prompts if arguments not supplied
        if not username:
            while True:
                username = input("Username: ").strip()
                if not username:
                    self.stdout.write(self.style.ERROR("Username cannot be empty."))
                    continue
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.ERROR(f"User '{username}' already exists. Choose another username."))
                    continue
                break
        elif User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists.")

        if not email:
            email = input("Email: ").strip()

        if not password:
            while True:
                p1 = getpass.getpass("Password: ")
                if not p1:
                    self.stdout.write(self.style.ERROR("Password cannot be empty."))
                    continue
                p2 = getpass.getpass("Confirm password: ")
                if p1 != p2:
                    self.stdout.write(self.style.ERROR("Passwords do not match. Try again."))
                    continue
                try:
                    validate_password(p1)
                except ValidationError as ve:
                    for err in ve.messages:
                        self.stdout.write(self.style.ERROR(f"  * {err}"))
                    continue
                password = p1
                break
        else:
            try:
                validate_password(password)
            except ValidationError as ve:
                raise CommandError(f"Password validation failed: {', '.join(ve.messages)}")

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(self.style.SUCCESS(f"\nAdmin user '{user.username}' created successfully!"))
        self.stdout.write(self.style.SUCCESS("You can now log in at /manage/login/"))
