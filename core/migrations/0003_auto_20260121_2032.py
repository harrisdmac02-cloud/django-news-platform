from django.db import migrations


def add_editor_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Use get_or_create to make it idempotent (safe to run multiple times)
    editors, created = Group.objects.get_or_create(name="Editor")

    try:
        # codename = change_article → comes from your Article model
        perm = Permission.objects.get(codename="change_article")
        editors.permissions.add(perm)
        print("Editor group updated with change_article permission")
    except Permission.DoesNotExist:
        print("Permission 'change_article' not found — maybe models not migrated yet?")
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_customuser_subscribed_journalists'),
    ]

    operations = [
        migrations.RunPython(add_editor_permissions),
    ]
