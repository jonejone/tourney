from django.contrib import admin
from tourney.tournament.models import (Tournament,
                                       TournamentPlayer,
                                       TournamentPage,
                                       TournamentNewsItem,
                                       TournamentClassPrice,
                                       TournamentOption,
                                       TournamentSite,
                                       TournamentAdmin,
                                       Player,
                                       PlayerClass,
                                       RegistrationStage,
                                       RegistrationStageClass,)


class TournamentSiteAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'site')


class TournamentAdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'tournament',)


class TournamentAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class TournamentPlayerAdmin(admin.ModelAdmin):
    list_display = ('player', 'tournament', 'player_class')


class RegistrationStageAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'opens')


class RegistrationStageClassAdmin(admin.ModelAdmin):
    list_display = ('registration_stage', 'player_class',
                    'rating_required')


class TournamentPageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('tournament', 'title', 'show_in_navigation',
                    'navigation_position',)


class TournamentOptionAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'name', 'price')


class TournamentClassPriceAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'player_class', 'price')


class TournamentNewsItemAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'title', 'created',
                    'is_published')


admin.site.register(TournamentPage, TournamentPageAdmin)
admin.site.register(TournamentNewsItem, TournamentNewsItemAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(TournamentOption, TournamentOptionAdmin)
admin.site.register(TournamentClassPrice, TournamentClassPriceAdmin)
admin.site.register(TournamentPlayer, TournamentPlayerAdmin)
admin.site.register(TournamentSite, TournamentSiteAdmin)
#admin.site.register(TournamentAdmin, TournamentAdminAdmin)
admin.site.register(Player)
admin.site.register(PlayerClass)
admin.site.register(RegistrationStage, RegistrationStageAdmin)
admin.site.register(RegistrationStageClass,
                    RegistrationStageClassAdmin)
