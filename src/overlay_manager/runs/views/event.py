import datetime

from django.views import generic
from django.contrib.auth import mixins as auth_mixins
from django import http
from django import urls

from overlay_manager.runs import models


class EventEditView(generic.DetailView):
    model = models.EventData
    template_name = "event/details.html"

    event: models.EventData

    def get_object(self, queryset=None, **kwargs) -> models.EventData:
        if not queryset:
            queryset = self.model.objects

        try:
            self.event = queryset.get(name=self.kwargs["event_name"])
            return self.event
        except self.model.DoesNotExist:
            raise http.Http404()

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["event"] = self.event
        ctx["current_run"] = self.event.current_run
        ctx["next_run"] = self.event.next_run
        ctx["runs"] = self.event.runs.filter(is_intermission=False)
        late = ""
        if late_seconds := self.event.shift.total_seconds():
            hours = int(late_seconds // 3600)
            minutes = int((late_seconds % 3600) // 60)
            if hours > 0:
                late += f"{hours}h "
            if minutes:
                late += f"{minutes}m"
        ctx["late"] = late

        return ctx


class MoveNextRunView(auth_mixins.PermissionRequiredMixin, generic.DetailView):
    model = models.EventData
    permission_required = "runs.change_eventdata"

    def get_object(self, queryset=None, **kwargs) -> models.EventData:
        if not queryset:
            queryset = self.model.objects

        try:
            return queryset.get(name=self.kwargs["event_name"])
        except self.model.DoesNotExist:
            raise http.Http404()

    def get(self, request, *args, **kwargs) -> http.HttpResponse:
        event = self.get_object()
        event.set_next_run()

        return http.HttpResponseRedirect(urls.reverse("event-details", kwargs={"event_name": event.name}))


class MovePreviousRunView(auth_mixins.PermissionRequiredMixin, generic.DetailView):
    model = models.EventData
    permission_required = "runs.change_eventdata"

    def get_object(self, queryset=None, **kwargs) -> models.EventData:
        if not queryset:
            queryset = self.model.objects

        try:
            return queryset.get(name=self.kwargs["event_name"])
        except self.model.DoesNotExist:
            raise http.Http404()

    def get(self, request, *args, **kwargs) -> http.HttpResponse:
        event = self.get_object()
        event.set_previous_run()

        return http.HttpResponseRedirect(urls.reverse("event-details", kwargs={"event_name": event.name}))


class DefaultEventRedirectView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs) -> str:
        next_event = models.EventData.objects.filter(event_end_on__lte=datetime.date.today()).earliest("event_start_on")
        return urls.reverse("event-details", kwargs={"event_name": next_event.name})
