# Generated by Django 5.0.6 on 2024-05-19 15:24

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runs", "0003_alter_run_event"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="run",
            name="is_current",
        ),
        migrations.AddField(
            model_name="eventdata",
            name="shift",
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
        migrations.AlterField(
            model_name="run",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="runs",
                to="runs.eventdata",
            ),
        ),
    ]
