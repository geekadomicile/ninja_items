from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Item, ComponentHistory, Note, File, Email, CodeIdentifier

@admin.register(ComponentHistory)
class ComponentHistoryAdmin(admin.ModelAdmin):
    list_display = ('item', 'action_type', 'old_parent', 'new_parent', 'changed_at')
    list_filter = ('action_type', 'changed_at')
    search_fields = ('item__name', 'old_parent__name', 'new_parent__name')
    date_hierarchy = 'changed_at'

@admin.register(Item)
class ItemMPTTAdmin(MPTTModelAdmin):
    list_display = ('name', 'qr_code', 'parent', 'created_at')
    search_fields = ('name', 'qr_code', 'description')
    list_filter = ('created_at',)

admin.site.register(Note)
admin.site.register(File)
admin.site.register(Email)
admin.site.register(CodeIdentifier)