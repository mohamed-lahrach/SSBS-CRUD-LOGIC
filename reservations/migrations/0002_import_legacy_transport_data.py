from django.db import migrations


def _noop(_apps, _schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("buses", "0001_initial"),
        ("routes", "0001_initial"),
        ("trips", "0001_initial"),
        ("reservations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            _noop,
            migrations.RunPython.noop,
        ),
    ]
