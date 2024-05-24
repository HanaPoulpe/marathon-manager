import logging

import obsws_python as obs
from django.conf import settings

logger = logging.getLogger("obs")


class ObsClientError(Exception):
    pass


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
            raise ObsClientError() from e

        return response.current_program_scene_name

    def set_scene(self, scene_name: str) -> None:
        try:
            self._ws.set_current_program_scene(scene_name)
            logger.info("Set OBS scene.", extra={"scene_name": scene_name})
        except Exception as e:
            logger.exception("Failed to set scene", exc_info=e)
            raise ObsClientError() from e

    def set_studio_scene(self, scene_name: str) -> None:
        try:
            self._ws.set_studio_mode_enabled(True)
            self._ws.set_current_preview_scene(scene_name)
            logger.info("Set OBS studio scene.", extra={"scene_name": scene_name})
        except Exception as e:
            logger.exception("Failed to set studio scene", exc_info=e)
            raise ObsClientError() from e

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
            raise ObsClientError() from e

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
            raise ObsClientError() from e
