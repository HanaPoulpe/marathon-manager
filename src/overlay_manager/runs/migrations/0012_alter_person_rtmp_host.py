# Generated by Django 5.2.1 on 2025-06-04 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runs", "0011_person_rtmp_host"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="rtmp_host",
            field=models.CharField(blank=True, null=True),
        ),
    ]
