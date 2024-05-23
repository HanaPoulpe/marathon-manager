import datetime
from typing import Optional

from django.db import models, transaction


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
    event_start_on = models.DateField(null=False, blank=False, default=datetime.date.today)
    event_end_on = models.DateField(null=False, blank=False, default=datetime.date.today)

    def __str__(self) -> str:
        return self.name

    @property
    def next_run(self) -> Optional["Run"]:
        current_run_index = 0
        if self.current_run is not None:
            current_run_index = self.current_run.run_index

        try:
            return Run.objects.filter(
                run_index__gt=current_run_index, is_intermission=False
            ).first()
        except Run.DoesNotExist:
            return None

    @property
    def next_slot(self) -> Optional["Run"]:
        current_run_index = 0
        if self.current_run is not None:
            current_run_index = self.current_run.run_index

        try:
            return Run.objects.filter(run_index__gt=current_run_index).first()
        except Run.DoesNotExist:
            return None

    @transaction.atomic
    def set_next_run(self) -> None:
        if not self.next_run:
            return

        now = datetime.datetime.now(datetime.UTC)

        if previous_run := self.current_run:
            previous_run.is_finished = True
            previous_run.actual_end_at = now
            previous_run.save()

        self.current_run = self.next_slot
        if current_run := self.current_run:
            current_run.actual_start_at = now
            delta = current_run.actual_start_at - current_run.planning_start_at
            self.shift = (
                delta if delta > datetime.timedelta(minutes=0) else datetime.timedelta(minutes=0)
            )
            current_run.save()

        self.save()

    @transaction.atomic
    def set_previous_run(self) -> None:
        if next_run := self.current_run:
            next_run.is_finished = False
            next_run.actual_start_at = None
            next_run.save()
        else:
            return

        current_run = (
            self.runs.filter(run_index__lt=next_run.run_index).order_by("-run_index").first()
        )
        if current_run:
            current_run.is_finished = False
            current_run.actual_end_at = None
            current_run.save()

        self.current_run = current_run
        self.save()


class Run(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    platform = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    trigger_warning = models.CharField(max_length=255, null=True, blank=True)

    estimated_time = models.DurationField(null=False, blank=False)
    planning_start_at = models.DateTimeField(null=False, blank=False)
    planning_end_at = models.DateTimeField(null=False, blank=False)
    actual_start_at = models.DateTimeField(null=True, blank=True)
    actual_end_at = models.DateTimeField(null=True, blank=True)

    event = models.ForeignKey(EventData, on_delete=models.CASCADE, related_name="runs")
    run_index = models.IntegerField(null=False, blank=False)

    runners = models.ManyToManyField(Person, related_name="runs", null=True)
    commentators = models.ManyToManyField(Person, related_name="comments")

    is_intermission = models.BooleanField(null=False, blank=False, default=False)
    is_finished = models.BooleanField(null=False, blank=False, default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "run_index"], name="run_order")]
        indexes = [models.Index(fields=["event", "run_index"])]

    def __str__(self) -> str:
        return f"{self.name} - {self.category} ({self.run_index})"

    @property
    def start_at(self) -> datetime.datetime:
        return self.actual_start_at or (self.planning_start_at + self.event.shift)
