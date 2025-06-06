import datetime

from django import http, urls
from django.contrib.auth import mixins as auth_mixins
from django.db import transaction
from django.db.models import Max
from django.views import generic

from overlay_manager.runs import forms, models
from overlay_manager.runs.operations import runs as run_operations
from overlay_manager.runs.operations import rtmp as rtmp_operations


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
        ctx["runs"] = self.event.runs.filter(is_intermission=False).order_by("run_index")
        late = ""
        if late_seconds := self.event.shift.total_seconds():
            hours = int(late_seconds // 3600)
            minutes = int((late_seconds % 3600) // 60)
            if hours > 0:
                late += f"{hours}h "
            if minutes:
                late += f"{minutes}m"
        ctx["late"] = late
        try:
            streams = rtmp_operations.get_active_streams()
        except rtmp_operations.CouldNotGetStats:
            streams = []
        ctx["streams"] = streams
        ctx["persons"] = models.Person.objects.all().order_by("name")

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
        run_operations.next_run_for_event(event)

        return http.HttpResponseRedirect(
            urls.reverse("event-details", kwargs={"event_name": event.name})
        )


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

        return http.HttpResponseRedirect(
            urls.reverse("event-details", kwargs={"event_name": event.name})
        )


class DefaultEventRedirectView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs) -> str:
        next_event = models.EventData.objects.filter(
            event_end_at__lte=datetime.date.today()
        ).earliest("event_start_at")
        return urls.reverse("event-details", kwargs={"event_name": next_event.name})


class EditRunPreviousView(auth_mixins.PermissionRequiredMixin, generic.DetailView):
    model = models.Run
    permission_required = "runs.change_eventdata"

    def get_object(self, queryset=None, **kwargs) -> tuple[models.Run | None, models.Run]:
        if not queryset:
            queryset = self.model.objects

        try:
            selected_run = queryset.get(id=self.kwargs["run_id"])
            previous_run = (
                selected_run.event.runs.filter(run_index__lt=selected_run.run_index)
                .order_by("-run_index")
                .first()
            )

            return previous_run, selected_run
        except self.model.DoesNotExist:
            raise http.Http404()

    @transaction.atomic
    def get(self, request, *args, **kwargs) -> http.HttpResponse:
        previous_run, selected_run = self.get_object()

        if not previous_run:
            return http.HttpResponseRedirect(
                urls.reverse("event-edit", kwargs={"event_name": selected_run.event.name})
            )

        previous_run_index = previous_run.run_index
        previous_run.run_index = -1
        previous_run.save()
        selected_run.run_index = previous_run_index
        selected_run.save()
        previous_run.run_index = selected_run.run_index + 1
        previous_run.save()
        run_operations.update_all_runs_for_events(selected_run.event)

        if previous_run == previous_run.event.current_run:
            previous_run.event.current_run = selected_run
            previous_run.event.save()

        return http.HttpResponseRedirect(
            urls.reverse("event-edit", kwargs={"event_name": selected_run.event.name})
        )


class EditRunNextView(auth_mixins.PermissionRequiredMixin, generic.DetailView):
    model = models.Run
    permission_required = "runs.change_eventdata"

    def get_object(self, queryset=None, **kwargs) -> tuple[models.Run, models.Run | None]:
        if not queryset:
            queryset = self.model.objects

        try:
            selected_run = queryset.get(id=self.kwargs["run_id"])
            next_run = (
                selected_run.event.runs.filter(run_index__gt=selected_run.run_index)
                .order_by("run_index")
                .first()
            )

            return selected_run, next_run
        except self.model.DoesNotExist:
            raise http.Http404()

    @transaction.atomic
    def get(self, request, *args, **kwargs) -> http.HttpResponse:
        selected_run, next_run = self.get_object()

        if not next_run:
            return http.HttpResponseRedirect(
                urls.reverse("event-edit", kwargs={"event_name": selected_run.event.name})
            )

        next_run_index = next_run.run_index
        next_run.run_index = -1
        next_run.save()
        selected_run.run_index = next_run_index
        selected_run.save()
        next_run.run_index = selected_run.run_index - 1
        next_run.save()
        run_operations.update_all_runs_for_events(selected_run.event)

        return http.HttpResponseRedirect(
            urls.reverse("event-edit", kwargs={"event_name": selected_run.event.name})
        )


class EventEditFormView(auth_mixins.PermissionRequiredMixin, generic.FormView):
    permission_required = "runs.change_eventdata"
    form_class = forms.EventForm
    model = models.EventData
    template_name = "event/edit.html"

    def get_object(self, queryset=None, **kwargs) -> models.EventData:
        if not queryset:
            queryset = self.model.objects

        try:
            return queryset.get(name=self.kwargs["event_name"])
        except self.model.DoesNotExist:
            raise http.Http404()

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        event = self.get_object()
        ctx["event"] = event
        ctx["runs"] = [
            {
                "id": run.id,
                "name": run.name,
                "estimated_time": run.estimated_time,
                "planning_start_at": run.planning_start_at,
                "planning_end_at": run.planning_end_at,
                "runners": run.runners.all(),
                "commentators": run.commentators.all(),
                "is_intermission": run.is_intermission,
                "is_finished": run.is_finished,
                "can_move_up": run.run_index > event.current_run.run_index,
                "can_move_down": run.run_index
                < event.runs.aggregate(Max("run_index"))["run_index__max"]
                and not run.is_finished,
            }
            for run in event.runs.order_by("run_index")
        ]
        try:
            streams = rtmp_operations.get_active_streams()
        except rtmp_operations.CouldNotGetStats:
            streams = []
        ctx["streams"] = streams
        ctx["persons"] = models.Person.objects.all().order_by("name")

        return ctx

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_success_url(self) -> str:
        return urls.reverse("event-edit", kwargs={"event_name": self.get_object().name})

    @transaction.atomic
    def post(self, request, *args, **kwargs) -> http.HttpResponse:
        self.event = self.get_object()
        form = self.get_form()

        if not form.is_valid():
            return self.form_invalid(form)

        self.event.event_start_at = form.cleaned_data["event_start_at"]
        self.event.event_end_at = form.cleaned_data["event_end_at"]
        self.event.shift = form.cleaned_data["shift"]
        self.event.current_run = form.cleaned_data["current_run"]
        self.event.name = form.cleaned_data["name"]
        self.event.save()
        run_operations.update_all_runs_for_events(self.event)

        return self.form_valid(form)
