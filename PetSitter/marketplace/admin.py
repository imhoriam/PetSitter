from django.contrib import admin
from .models import SitterProfile, Service, SitterService, Pet, Booking
# Register your models here.

admin.site.register(SitterProfile)
admin.site.register(Service)
admin.site.register(SitterService)
admin.site.register(Pet)
admin.site.register(Booking)