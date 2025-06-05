from collections.abc import Generator
import dataclasses
import requests
from xml.etree import ElementTree

from django.conf import settings
from django.db.models import Q

from overlay_manager.runs import models


class CouldNotGetStats(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class Stream:
    id: str
    url: str
    runner: models.Person | None

    def __str__(self) -> str:
        return self.id


def get_active_streams() -> Generator[Stream, None, None]:
    stats = _get_stats(settings.RTMP_STATS_URI)
    et = _parse_stats(stats)

    for stream in et.findall("server/application/live/stream"):
        stream_id = stream.find("name").text
        stream_url = f"{settings.RTMP_BASE_URI}/{stream_id}"
        runner_q = models.Person.objects.filter(
            Q(rtmp_host__in=[stream_id, stream_url]) | Q(name=stream_id)
        )

        try:
            runner = runner_q.first()
        except models.Person.DoesNotExist:
            runner = None

        yield Stream(
            id=stream_id,
            url=stream_url,
            runner=runner,
        )


def _get_stats(url: str) -> str:
    stats = requests.get(settings.RTMP_STATS_URI)
    if not stats.ok:
        raise CouldNotGetStats()

    return stats.text


def _parse_stats(stats: str) -> ElementTree:
    try:
        return ElementTree.fromstring(stats)
    except ElementTree.ParseError as e:
        raise CouldNotGetStats() from e
