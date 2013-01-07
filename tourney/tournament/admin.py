from django.contrib import admin
from tourney.tournament.models import ( Tournament,
                                        TournamentPlayer,
                                        Player,
                                        PlayerClass,)


class TournamentAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    

admin.site.register(Tournament, TournamentAdmin)
admin.site.register(TournamentPlayer)
admin.site.register(Player)
admin.site.register(PlayerClass)

