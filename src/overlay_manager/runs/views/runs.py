from django.views import generic
from django import http

from overlay_manager.runs import models


class CurrentRunView(generic.DetailView):
    model = models.EventData

    def get_object(self, queryset=None, **kwargs) -> models.Run:
        if not queryset:
            queryset = self.model.objects

        try:
            return queryset.get(name=self.kwargs["event_name"]).current_run
        except self.model.DoesNotExist:
            raise http.Http404()


class CurrentRunNameView(CurrentRunView):
    template_name = "current/run_name.html"


class CurrentRunCategoryView(CurrentRunView):
    template_name = "current/run_category.html"


class CurrentRunPlatformView(CurrentRunView):
    template_name = "current/run_platform.html"


class CurrentRunEstimateView(CurrentRunView):
    template_name = "current/run_estimate.html"


class CurrentRunnerView(CurrentRunView):
    def get_object(self, queryset=None, **kwargs) -> models.Person:
        run = super().get_object()
        runners = [r for r in run.runners.all().order_by("id")]

        try:
            return runners[self.kwargs["index"]]
        except IndexError:
            raise http.Http404()


class CurrentRunnerNameView(CurrentRunnerView):
    template_name = "current/runner_name.html"


class CurrentRunnerPronounsView(CurrentRunnerView):
    template_name = "current/runner_pronouns.html"


class NextRunView(CurrentRunView):
    template_name = "next/run.html"

    def get_object(self, queryset=None, **kwargs) -> models.Run | None:
        if not queryset:
            queryset = self.model.objects

        try:
            event = queryset.get(name=self.kwargs["event_name"])
            return (
                event.runs.filter(
                    run_index__gt=event.current_run.run_index,
                    is_intermission=False,
                )
                .prefetch_related("runners")
                .first()
            )
        except self.model.DoesNotExist:
            return None

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["runners"] = self.object.runners.all().order_by("id")

        return ctx
