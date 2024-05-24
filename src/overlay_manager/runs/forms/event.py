from django import forms

from overlay_manager.runs import models


class EventForm(forms.ModelForm):
    class Meta:
        model = models.EventData
        fields = ["name", "event_start_at", "event_end_at", "shift", "current_run"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["current_run"].choices = [
                (run.id, run.name)
                for run in models.Run.objects.filter(is_finished=False, event=self.instance)
            ]
        else:
            self.fields["current_run"].choices = []
