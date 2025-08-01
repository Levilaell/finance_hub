# Generated manually for simplification
from django.db import migrations


def simplify_models(apps, schema_editor):
    """
    This is a manual migration to simplify the companies app.
    Since we're removing many fields and models, we'll handle this carefully.
    """
    # The actual schema changes will be handled by the next migration
    # This is just to mark the transition
    pass


def reverse_simplify(apps, schema_editor):
    """
    Reversal would require restoring all the removed fields and models
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(simplify_models, reverse_simplify),
    ]