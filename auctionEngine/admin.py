from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Auction, Bid

admin.site.register(User, UserAdmin)
admin.site.register(Auction)
admin.site.register(Bid)