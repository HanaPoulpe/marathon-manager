from django.contrib import admin

from . import models

admin.site.register(models.Person)
admin.site.register(models.Run)
admin.site.register(models.EventData)
