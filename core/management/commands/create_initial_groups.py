from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from core.models import Article  # ← import your Article model


class Command(BaseCommand):
    """
    Creates initial permission groups for the news application:
    - Reader
    - Journalist
    - Editor

    Run with:
    python manage.py create_initial_groups
    """

    help = 'Creates/Updates initial groups and permissions for Reader, Journalist, Editor'

    def handle(self, *args, **options):
        # Get content type for Article model
        article_ct = ContentType.objects.get_for_model(Article)

        # Get all useful article permissions
        all_article_perms = Permission.objects.filter(content_type=article_ct)

        # Useful individual permissions
        perms = {
            'view': Permission.objects.get(codename='view_article', content_type=article_ct),
            'add': Permission.objects.get(codename='add_article', content_type=article_ct),
            'change': Permission.objects.get(codename='change_article', content_type=article_ct),
            'delete': Permission.objects.get(codename='delete_article', content_type=article_ct),
        }

        # ── Reader ───────────────────────────────────────────────────────
        reader_group, created = Group.objects.get_or_create(name='Reader')

        if created:
            self.stdout.write(self.style.SUCCESS('Created Reader group'))
        else:
            self.stdout.write('Reader group already exists → updating permissions')

        reader_group.permissions.clear()
        reader_group.permissions.add(perms['view'])

        # ── Journalist ───────────────────────────────────────────────────
        journalist_group, created = Group.objects.get_or_create(name='Journalist')

        if created:
            self.stdout.write(self.style.SUCCESS('Created Journalist group'))
        else:
            self.stdout.write('Journalist group already exists → updating permissions')

        journalist_group.permissions.clear()
        journalist_group.permissions.add(
            perms['view'],
            perms['add'],
            perms['change'],
            perms['delete'],
        )

        # ── Editor ───────────────────────────────────────────────────────
        # Editors usually get the same CRUD as journalists + can approve/publish
        # (approval is usually done via custom view + business logic, not a separate permission)
        editor_group, created = Group.objects.get_or_create(name='Editor')

        if created:
            self.stdout.write(self.style.SUCCESS('Created Editor group'))
        else:
            self.stdout.write('Editor group already exists → updating permissions')

        editor_group.permissions.clear()
        editor_group.permissions.add(
            perms['view'],
            perms['add'],
            perms['change'],
            perms['delete'],
        )

        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('  Initial groups & permissions created/updated successfully  '))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(f"• Reader:     can view published articles")
        self.stdout.write(f"• Journalist: can CRUD own articles")
        self.stdout.write(f"• Editor:     can CRUD all articles + approve/publish")
        self.stdout.write(self.style.SUCCESS('═' * 60) + '\n')