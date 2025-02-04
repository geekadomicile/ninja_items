from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Item, ComponentHistory, Note, Attachment, Email

admin.site.register(Item, MPTTModelAdmin)
admin.site.register(ComponentHistory)
admin.site.register(Note)
admin.site.register(Attachment)
admin.site.register(Email)