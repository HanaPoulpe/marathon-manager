from django.contrib import admin
from django import urls

from overlay_manager.runs import views

urlpatterns = [
    urls.path("admin/", admin.site.urls),
    urls.path("accounts/", urls.include("allauth.urls")),
    # Current run
    urls.path(
        "event/<str:event_name>/current/run_name",
        views.CurrentRunNameView.as_view(),
        name="current-run-name",
    ),
    urls.path(
        "event/<str:event_name>/current/run_category",
        views.CurrentRunCategoryView.as_view(),
        name="current-run-category",
    ),
    urls.path(
        "event/<str:event_name>/current/run_platform",
        views.CurrentRunPlatformView.as_view(),
        name="current-run-platform",
    ),
    urls.path(
        "event/<str:event_name>/current/run_estimate",
        views.CurrentRunEstimateView.as_view(),
        name="current-run-estimate",
    ),
    urls.path(
        "event/<str:event_name>/current/runner/<int:index>/name",
        views.CurrentRunnerNameView.as_view(),
        name="current-runner-name",
    ),
    urls.path(
        "event/<str:event_name>/current/runner/<int:index>/pronouns",
        views.CurrentRunnerPronounsView.as_view(),
        name="current-runner-pronouns",
    ),
    urls.path(
        "event/<str:event_name>/current/runner/<int:index>/name_and_pronouns",
        views.CurrentRunnerNameAndPronounsView.as_view(),
        name="current-runner-name-and-pronouns",
    ),
    # Next run
    urls.path(
        "event/<str:event_name>/next/run",
        views.NextRunView.as_view(),
        name="next-run",
    ),
    # Event Management
    urls.path(
        "event/<str:event_name>/details",
        views.EventEditView.as_view(),
        name="event-details",
    ),
    urls.path(
        "event/<str:event_name>/move-next",
        views.MoveNextRunView.as_view(),
        name="event-move-next",
    ),
    urls.path(
        "event/<str:event_name>/move-previous",
        views.MovePreviousRunView.as_view(),
        name="event-move-previous",
    ),
    # Default URL
    urls.path("", views.DefaultEventRedirectView.as_view(), name="default-event")
]
