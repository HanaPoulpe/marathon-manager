import datetime
import logging

from django.db import transaction

from overlay_manager.runs import models
from overlay_manager.vendors.obs import client as obs_client

logger = logging.getLogger("runs")


@transaction.atomic
def update_run_dates(run: models.Run) -> None:
    if run.actual_end_at:
        return

    previous_run = (
        models.Run.objects.filter(run_index__lt=run.run_index, event=run.event)
        .order_by("-run_index")
        .first()
    )

    run.planning_start_at = (
        previous_run.planning_end_at if previous_run else run.event.event_start_at
    )
    run.planning_end_at = run.planning_start_at + run.estimated_time
    run.save()


@transaction.atomic
def update_all_runs_for_events(event: models.EventData) -> None:
    for run in event.runs.order_by("run_index"):
        update_run_dates(run)


@transaction.atomic(durable=True)
def next_run_for_event(event: models.EventData) -> None:
    if not event.next_slot:
        logger.info(
            "No next slot for event", extra={"event": event, "current_run": event.current_run}
        )
        return

    with transaction.atomic():
        current_run = event.current_run

        now = datetime.datetime.now(datetime.UTC)
        if previous_run := current_run:
            previous_run.is_finished = True
            previous_run.actual_end_at = now
            previous_run.save()

        event.current_run = event.next_slot
        if current_run := event.current_run:
            current_run.actual_start_at = now
            delta = current_run.actual_start_at - current_run.planning_start_at
            event.shift = (
                delta if delta > datetime.timedelta(minutes=0) else datetime.timedelta(minutes=0)
            )
            current_run.save()

        event.save()

    if not current_run:
        return

    try:
        obs = obs_client.ObsClient()
        if scene_id := current_run.obs_scene_id:
            obs.set_scene(scene_id)

        next_run = event.next_slot
        if next_run and (scene_id := next_run.obs_scene_id):
            obs.set_studio_scene(scene_id)

            if next_run.is_intermission:
                _update_intermission(obs, next_run)
            else:
                _update_run(obs, next_run)

    except obs_client.ObsClientError as e:
        logger.exception(
            "Failed to update OBS",
            exc_info=e,
            extra={"event": event, "current_run": current_run, "next_run": event.next_run},
        )


def _update_intermission(obs: obs_client.ObsClient, run: models.Run) -> None:
    next_runs_display = ["next_run_1", "next_run_2", "next_run_3"]
    timer_start_value = max(
        run.planning_end_at - datetime.datetime.now(datetime.UTC), run.estimated_time
    )

    for scene, run in zip(next_runs_display, run.event.runs.order_by("run_index")):
        try:
            obs.set_text_source_text(scene, run.name)
        except obs_client.ObsClientError:
            pass

    # TODO: set timer


def _update_run(obs: obs_client.ObsClient, run: models.Run):
    runners_name_display = [
        ["runner_0_0"],
        ["runner_1_0"],
        ["runner_2_0"],
        ["runner_3_0"],
    ]
    commentators_name_display = [
        ["commentator_0_0"],
        ["commentator_1_0"],
        ["commentator_2_0"],
        ["commentator_3_0"],
    ]
    runners_pronouns_display = [
        ["runner_pronouns_0_0"],
        ["runner_pronouns_1_0"],
        ["runner_pronouns_2_0"],
        ["runner_pronouns_3_0"],
    ]
    commentators_pronouns_display = [
        ["commentator_pronouns_0_0"],
        ["commentator_pronouns_1_0"],
        ["commentator_pronouns_2_0"],
        ["commentator_pronouns_3_0"],
    ]
    runners_socials_media_display = [
        [],
        [],
        [],
        [],
    ]
    run_title_displays = ["run_title_0", "run_title_1"]
    run_category_displays = ["run_category_0", "run_category_1"]
    run_platform_displays = ["run_platform_0", "run_platform_1"]
    run_estimated_time_displays = ["run_estimated_time_0", "run_estimated_time_1"]
    next_run_displays = ["next_run_0", "next_run_1"]

    for runner_name, runner_pronouns, runner_socials_media, runner in zip(
        runners_name_display,
        runners_pronouns_display,
        runners_socials_media_display,
        run.runners.order_by("name"),
    ):
        for scene in runner_name:
            obs.set_text_source_text(scene, runner.name)
        for scene in runner_pronouns:
            obs.set_text_source_text(scene, runner.pronouns or "")
        for scene in runner_socials_media:
            pass  # TODO

    for commentator_name, commentator_pronouns, commentator in zip(
        commentators_name_display, commentators_pronouns_display, run.commentators.order_by("name")
    ):
        for scene in commentator_name:
            obs.set_text_source_text(scene, commentator.name)
        for scene in commentator_pronouns:
            obs.set_text_source_text(scene, commentator.pronouns or "")

    for scene in run_title_displays:
        obs.set_text_source_text(scene, run.name)
    for scene in run_category_displays:
        obs.set_text_source_text(scene, run.category)
    for scene in run_platform_displays:
        obs.set_text_source_text(scene, run.platform)
    for scene in run_estimated_time_displays:
        obs.set_text_source_text(
            scene,
            f"{run.estimated_time.seconds // 3600}:"
            f"{run.estimated_time.seconds % 3600 // 60:02}:"
            f"{run.estimated_time.seconds % 60:02}",
        )

    next_run = (
        run.event.runs.filter(run_index__gt=run.run_index, intermission=False)
        .order_by("run_index")
        .first()
    )
    if not next_run:
        return
    for scene in next_run_displays:
        obs.set_text_source_text(scene, next_run.name)
