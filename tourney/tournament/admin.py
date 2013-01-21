from django.contrib import admin
from tourney.tournament.models import ( Tournament,
                                        TournamentPlayer,
                                        TournamentPage,
                                        Player,
                                        PlayerClass,
                                        RegistrationStage,
                                        RegistrationStageClass,)


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


admin.site.register(TournamentPage, TournamentPageAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(TournamentPlayer, TournamentPlayerAdmin)
admin.site.register(Player)
admin.site.register(PlayerClass)
admin.site.register(RegistrationStage, RegistrationStageAdmin)
admin.site.register(RegistrationStageClass,
    RegistrationStageClassAdmin)
