import logging

import attrs
import obsws_python as obs
from django.conf import settings

logger = logging.getLogger("obs")


class ObsClientError(Exception):
    pass


@attrs.define
class SourcePosition:
    scene_id: str
    scene_item_id: int
    alignment: int
    bounds_alignment: int
    bounds_height: int
    bounds_type: str
    crop_bottom: int
    crop_left: int
    crop_right: int
    crop_top: int
    height: float
    position_x: float
    position_y: float
    rotation: float
    scale_x: float
    scale_y: float
    source_height: float
    source_width: float
    width: float


class ObsClient:
    def __init__(self) -> None:
        self._host = settings.OBS_HOST
        self._port = settings.OBS_PORT
        self._password = settings.OBS_PASSWORD
        self._ws = obs.ReqClient(host=self._host, port=self._port, password=self._password)

    def get_current_scene(self) -> str:
        try:
            response = self._ws.get_current_program_scene()
            logger.info("Got OBS current scene.", extra=response.__dict__)
        except Exception as e:
            logger.exception("Failed to get current scene", exc_info=e)
            # raise ObsClientError() from e
            return ""

        return response.current_program_scene_name

    def set_scene(self, scene_name: str) -> None:
        try:
            self._ws.set_current_program_scene(scene_name)
            logger.info("Set OBS scene.", extra={"scene_name": scene_name})
        except Exception as e:
            logger.exception("Failed to set scene", exc_info=e)
            # raise ObsClientError() from e

    def set_studio_scene(self, scene_name: str) -> None:
        try:
            self._ws.set_studio_mode_enabled(True)
            self._ws.set_current_preview_scene(scene_name)
            logger.info("Set OBS studio scene.", extra={"scene_name": scene_name})
        except Exception as e:
            logger.exception("Failed to set studio scene", exc_info=e)
            # raise ObsClientError() from e

    def get_all_scenes(self) -> list[str]:
        try:
            response = self._ws.get_scene_list()
            logger.info("Got OBS scenes.", extra=response.__dict__)
        except Exception as e:
            logger.exception("Failed to get scenes", exc_info=e)
            raise ObsClientError() from e

        return [scene["sceneName"] for scene in response.scenes]

    def set_text_source_text(self, source_name: str, text: str) -> None:
        try:
            self._ws.set_input_settings(
                name=source_name,
                settings={"text": text},
                overlay=True,
            )
            logger.info(
                "Set OBS text source text.", extra={"source_name": source_name, "text": text}
            )
        except Exception as e:
            logger.exception("Failed to set text source text", exc_info=e)
            # raise ObsClientError() from e

    def get_scene_sources(self, scene_name: str) -> list:
        try:
            response = self._ws.get_scene_item_list(scene_name)
            logger.info("Got OBS scene sources.", extra=response.__dict__)
        except Exception as e:
            logger.exception("Failed to get scene sources", exc_info=e)
            # raise ObsClientError() from e
            return []

        return response.scene_items

    def get_scene_source_position(
        self, scene_name: str, source_name: str
    ) -> SourcePosition | None:
        for source in self.get_scene_sources(scene_name):
            if source["sourceName"] == source_name:
                return SourcePosition(
                    scene_id=scene_name,
                    scene_item_id=source["sceneItemId"],
                    alignment=source["sceneItemTransform"]["alignment"],
                    bounds_alignment=source["sceneItemTransform"]["boundsAlignment"],
                    bounds_height=source["sceneItemTransform"]["boundsHeight"],
                    bounds_type=source["sceneItemTransform"]["boundsType"],
                    crop_bottom=source["sceneItemTransform"]["cropBottom"],
                    crop_left=source["sceneItemTransform"]["cropLeft"],
                    crop_right=source["sceneItemTransform"]["cropRight"],
                    crop_top=source["sceneItemTransform"]["cropTop"],
                    height=source["sceneItemTransform"]["height"],
                    position_x=source["sceneItemTransform"]["positionX"],
                    position_y=source["sceneItemTransform"]["positionY"],
                    rotation=source["sceneItemTransform"]["rotation"],
                    scale_x=source["sceneItemTransform"]["scaleX"],
                    scale_y=source["sceneItemTransform"]["scaleY"],
                    source_height=source["sceneItemTransform"]["sourceHeight"],
                    source_width=source["sceneItemTransform"]["sourceWidth"],
                    width=source["sceneItemTransform"]["width"],
                )
        return None

    def set_scene_source_position(self, position: SourcePosition) -> None:
        scene_item_transform = {
            "alignment": position.alignment,
            "boundsAlignment": position.bounds_alignment,
            "boundsType": position.bounds_type,
            "cropBottom": position.crop_bottom,
            "cropLeft": position.crop_left,
            "cropRight": position.crop_right,
            "cropTop": position.crop_top,
            "height": position.height,
            "positionX": position.position_x,
            "positionY": position.position_y,
            "rotation": position.rotation,
            "scaleX": position.scale_x,
            "scaleY": position.scale_y,
            "scaleHeight": position.source_height,
            "scaleWidth": position.source_width,
            "width": position.width,
        }
        if position.bounds_height:
            scene_item_transform["boundsHeight"] = position.bounds_height
        try:
            self._ws.set_scene_item_transform(
                scene_name=position.scene_id,
                item_id=position.scene_item_id,
                transform=scene_item_transform,
            )
            logger.info(
                "Set OBS scene source position.",
                extra={
                    "position": position,
                },
            )
        except Exception as e:
            logger.exception("Failed to set scene source position", exc_info=e)
            # raise ObsClientError() from e

    def set_rtmp_source_url(self, source_name: str, url: str) -> None:
        try:
            self._ws.set_input_settings(
                name=source_name,
                settings={
                    "input": url,
                },
                overlay=True,
            )
            logger.info("Set OBS rtmp source url.", extra={"source_name": source_name, "url": url})
        except Exception as e:
            logger.exception("Failed to set rtmp source url", exc_info=e)
            # raise ObsClientError() from e
