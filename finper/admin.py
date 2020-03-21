from django.contrib import admin

# Register your models here.
from .models import Movement, Account

admin.site.register(Movement)
admin.site.register(Account)