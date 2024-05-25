from django import http
from django.contrib.auth import mixins as auth_mixins
from django.views import generic

from overlay_manager.vendors.obs import client

from .runs import CurrentRunView


class ScreenshotView(auth_mixins.PermissionRequiredMixin, CurrentRunView):
    content_type = "image/png"
    permission_required = "runs.view_eventdata"

    def get(self, request, *args, **kwargs) -> http.HttpResponse:
        run = self.get_object()
        obs = client.ObsClient()

        try:
            img = obs.get_source_screen_shot(run.obs_scene_id)
            return http.HttpResponse(img, content_type=self.content_type)
        except client.ObsClientError:
            return http.HttpResponseNotFound()
