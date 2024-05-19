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
        name="current_run_name",
    ),
    urls.path(
        "event/<str:event_name>/current/run_category",
        views.CurrentRunCategoryView.as_view(),
        name="current_run_category",
    ),
    urls.path(
        "event/<str:event_name>/current/run_platform",
        views.CurrentRunPlatformView.as_view(),
        name="current_run_platform",
    ),
    urls.path(
        "event/<str:event_name>/current/run_estimate",
        views.CurrentRunEstimateView.as_view(),
        name="current_run_estimate",
    ),
    urls.path(
        "event/<str:event_name>/current/runner/<int:index>/name",
        views.CurrentRunnerNameView.as_view(),
        name="current_runner_name",
    ),
    urls.path(
        "event/<str:event_name>/current/runner/<int:index>/pronouns",
        views.CurrentRunnerPronounsView.as_view(),
        name="current_runner_pronouns",
    ),
    # Next run
    urls.path(
        "event/<str:event_name>/next/run",
        views.NextRunView.as_view(),
        name="next_run",
    ),
    # Event Management
]
