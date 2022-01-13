from django.db import models
from django.forms import TextInput, Textarea
from django.contrib import admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from reversion.admin import VersionAdmin
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
from .models import User, Room, Name_item, Count_item, Event, Coworking_Slot, Coworking_People, Issue

admin.sites.AdminSite.site_header = 'Центр опережающей профессиональной подготовки'
admin.sites.AdminSite.site_title = 'Центр опережающей профессиональной подготовки'
admin.sites.AdminSite.index_title = 'Администрирование сайта'


def duplicate_event(modeladmin, request, queryset):
    for object in queryset:
        object.id = None
        object.save()
duplicate_event.short_description = "Дублировать"


class IssueInstanceInline(admin.TabularInline):
    model = Issue
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 40})},
    }

@admin.register(User)
class UserViews(VersionAdmin, SimpleHistoryAdmin):
    list_display = ('first_name', 'last_name', 'type', 'organization', 'email', 'phone', 'registration_date', 'registration_time', 'status', )
    list_editable = ('status',)
    list_filter = ('status', 'type')
    search_fields = ('first_name', 'last_name','organization', 'email', 'phone')
    # fields = ()
    # readonly_fields = ()
    inlines = [IssueInstanceInline]


class Count_itemInstanceInline(admin.TabularInline):
     model = Count_item
     extra = 0


@admin.register(Room)
class RoomViews(VersionAdmin):
    list_display = ('name_room', 'max_people', 'description_room')
    inlines = [Count_itemInstanceInline]


@admin.register(Name_item)
class Name_itemViews(VersionAdmin):
    list_display = ('name_item',)


@admin.register(Count_item)
class Count_itemViews(VersionAdmin):
    list_display = ('room_id', 'item_id', 'count_item')


@admin.register(Event)
class EventViews(VersionAdmin):
    list_display = ('name_event', 'user_id', 'organization', 'quantity_people', 'date', 'start_time', 'finish_time', 'status', )
    list_editable = ('quantity_people', 'status')
    list_filter = ('status', ('date', DateRangeFilter))
    search_fields = ('name_event',)
    actions = [duplicate_event]


class Coworking_PeopleInstanceInline(admin.TabularInline):
    model = Coworking_People
    extra = 0
  # max_num = 20


@admin.register(Coworking_Slot)
class Coworking_SlotViews(VersionAdmin):
    list_display = ('number_slot', 'user_id_created', 'quantity_people', 'room_id', 'date', 'start_time', 'finish_time', 'status')
    inlines = [Coworking_PeopleInstanceInline]
    list_editable = ('status',)
    list_filter = ('room_id','status')
    search_fields = ('number_slot',)


@admin.register(Coworking_People)
class Coworking_PeopleViews(VersionAdmin):
    list_display = ('slot_id', 'full_name', 'email', 'phone', 'user_id_add', 'status_people', 'visited')
    list_editable = ('status_people', 'visited')
    list_filter = ('status_people', 'visited')
    search_fields = ('full_name', 'email', 'phone')

@admin.register(Issue)
class IssueViews(VersionAdmin):
    list_display = ('user_id', 'type', 'connection','message_from_user', 'message_from_employee', 'date', 'time', 'status')
    list_editable = ('type', 'status', 'message_from_employee')
    list_filter = ('status', 'type')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 25})},
    }

