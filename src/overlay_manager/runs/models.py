import datetime

from django.db import models


class Person(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    pronouns = models.CharField(max_length=255, null=True, blank=True)
    socials = models.URLField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class EventData(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    current_run = models.ForeignKey("Run", null=True, blank=True, on_delete=models.SET_NULL)
    shift = models.DurationField(null=False, blank=False, default=datetime.timedelta(minutes=0))

    def __str__(self) -> str:
        return self.name


class Run(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    platform = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)

    estimated_time = models.DurationField(null=False, blank=False)
    planning_start_at = models.DateTimeField(null=False, blank=False)
    planning_end_at = models.DateTimeField(null=False, blank=False)
    actual_start_at = models.DateTimeField(null=True, blank=True)
    actual_end_at = models.DateTimeField(null=True, blank=True)

    event = models.ForeignKey(EventData, on_delete=models.CASCADE, related_name="runs")
    run_index = models.IntegerField(null=False, blank=False)

    runners = models.ManyToManyField(Person, related_name="runs")
    commenters = models.ManyToManyField(Person, related_name="comments")

    is_intermission = models.BooleanField(null=False, blank=False, default=False)
    is_finished = models.BooleanField(null=False, blank=False, default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "run_index"], name="run_order")]
        indexes = [models.Index(fields=["event", "run_index"])]

    def __str__(self) -> str:
        return f"{self.name} - {self.category} ({self.run_index})"
