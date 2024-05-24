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

    event.set_next_run()
    current_run = event.current_run

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
    next_runs_display = [
        (
            "Titre_NextRun",
            "Categorie_NextRun",
            "Runneureuse_1_NextRun",
            "Runneureuse_1_Pronoms_NextRun",
            "Estimate_NextRun",
        ),
        (
            "Titre_Next",
            "Categorie_Next",
            "Runneureuse_1_Next",
            "Runneureureuse_1_Pronoms_Next",
            "Estimate_Next",
        ),
        (
            "Titre_Next2",
            "Categorie_Next2",
            "Runneureuse_1_Next2",
            "Runneureuse_1_Pronoms_Next2",
            "Estimate_Next2",
        ),
        (
            "Titre_Next3",
            "Categorie_Next3",
            "Runneureuse_1_Next3",
            "Runneureuse_1_Pronoms_Next3",
            "Estimate_Next3",
        ),
    ]
    timer_start_value = max(
        run.planning_end_at - datetime.datetime.now(datetime.UTC), run.estimated_time
    )
    scene = "Intermission"

    for run, displays in zip(
        models.Run.objects.filter(
            is_intermission=False, run_index__gt=run.run_index, event=run.event
        ).order_by("run_index"),
        next_runs_display,
    ):
        try:
            obs.set_text_source_text(displays[0], run.name)
            obs.set_text_source_text(displays[1], run.category or "")
            obs.set_text_source_text(displays[2], run.runners.first().name)
            obs.set_text_source_text(displays[3], run.runners.first().pronouns or "")
            obs.set_text_source_text(
                displays[4],
                f"{run.estimated_time.seconds // 3600}:"
                f"{run.estimated_time.seconds % 3600 // 60:02}:"
                f"{run.estimated_time.seconds % 60:02}",
            )
        except obs_client.ObsClientError:
            pass

    # TODO: set timer


def _update_run(obs: obs_client.ObsClient, run: models.Run):
    runners_name_display = [
        ["Runneureuse_1_1P_4:3", "Runneureuse_1_1P_WS"],
        ["Runneureuse_2"],
        ["Runneureuse_3"],
        ["Runneureuse_3"],
    ]
    commentators_name_display = [
        ["Commentateurice_1_1P_4:3", "Commentateur_1_1P_WS"],
        ["Commentateurice_2_1P_4:3", "Commentateur_2_1P_WS"],
    ]
    runners_pronouns_display = [
        ["Runneureuse_1_Pronoms_4:3", "Runneureuse_1_Pronoms_WS"],
        [],
        [],
        [],
    ]
    commentators_pronouns_display = [
        ["Commentateurice_1_Pronoms_4:3", "Commentateurice_1_Pronoms_WS"],
        ["Commentateurice_2_Pronoms_4:3", "Commentateurice_2_Pronoms_WS"],
    ]
    runners_socials_media_display = [
        [],
        [],
        [],
        [],
    ]
    run_title_displays = ["Titre_1P_WS", "Titre_1P_4:3", "Titre_4P"]
    run_category_displays = ["Categorie_1P_WS", "Categorie_1P_4:3", "Categorie_4P"]
    run_platform_displays = ["Support/Année_1P_WS", "Support/Année_1P_4:3", "Support/Année_4P"]
    run_estimated_time_displays = ["Estimate"]
    next_run_displays = []

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
        obs.set_text_source_text(scene, run.category or "")
    for scene in run_platform_displays:
        obs.set_text_source_text(scene, run.platform or "")
    for scene in run_estimated_time_displays:
        obs.set_text_source_text(
            scene,
            f"{run.estimated_time.seconds // 3600}:"
            f"{run.estimated_time.seconds % 3600 // 60:02}:"
            f"{run.estimated_time.seconds % 60:02}",
        )

    next_run = (
        run.event.runs.filter(run_index__gt=run.run_index, is_intermission=False)
        .order_by("run_index")
        .first()
    )
    if not next_run:
        return
    for scene in next_run_displays:
        obs.set_text_source_text(scene, next_run.name)


def _replace_runner_elements_for_scene(
    obs: obs_client.ObsClient,
    scene: str,
    runner: models.Person,
    name_scene_id: str,
    pronouns_scene_id: str,
    socials_media_scene_id: str,
) -> None:
    if scene != "1P - 4/3":
        return

    margin = 5
    max_x = 128

    runner_name_position = obs.get_scene_source_position(scene, name_scene_id)
    runner_pronouns_position = obs.get_scene_source_position(scene, pronouns_scene_id)

    new_x_position = runner_name_position.position_x + margin + runner_pronouns_position.width

    if new_x_position <= max_x:
        runner_pronouns_position.position_x = new_x_position
        runner_pronouns_position.position_y = (
            runner_name_position.position_y
            + runner_name_position.height
            - runner_pronouns_position.height
        )
    else:
        runner_pronouns_position.position_y = (
            runner_name_position.position_y + runner_name_position.height + margin
        )
        runner_pronouns_position.position_x = (
            runner_name_position.position_x
            + runner_name_position.width / 2
            - runner_pronouns_position.width / 2
        )

    obs.set_scene_source_position(runner_pronouns_position)
