from django.db import transaction

from overlay_manager.runs import models


@transaction.atomic
def update_run_dates(run: models.Run) -> None:
    if run.actual_end_at:
        return

    previous_run = models.Run.objects.filter(run_index__lt=run.run_index, event=run.event).order_by("-run_index").first()

    run.planning_start_at = previous_run.planning_end_at if previous_run else run.event.event_start_at
    run.planning_end_at = run.planning_start_at + run.estimated_time
    run.save()


@transaction.atomic
def update_all_runs_for_events(event: models.EventData) -> None:
    for run in event.runs.order_by("run_index"):
        update_run_dates(run)
