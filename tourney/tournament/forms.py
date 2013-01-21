from django import forms
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from datetime import datetime

from .models import (   Player,
                        PlayerClass,
                        TournamentPlayer,
                        TournamentPage,)


class TournamentPageForm(forms.ModelForm):
    def __init__(self, *kargs, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))
        self.helper.form_class = 'edit-page-form'

        if kwargs.get('instance'):
            self.helper.form_action = reverse(
                'tournament-page-edit', args=[
                kwargs.get('instance').slug])
        else:
            self.helper.form_action = reverse(
                'tournament-page-create')

        super(TournamentPageForm, self).__init__(*kargs, **kwargs)

    class Meta:
        model = TournamentPage
        fields = ('title', 'body', 'show_in_navigation',
            'navigation_position')


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = (
            'pdga_number', 'name', 'email',
            'phonenumber')


class RegistrationForm(PlayerForm):
    player_class = forms.ChoiceField()

    class Meta:
        model = Player
        fields = ('player_class', 'pdga_number',
            'name', 'country', 'email', 'phonenumber')

    def __init__(self, *kargs, **kwargs):

        if kwargs.get('tournament'):
            self.tournament = kwargs.get('tournament')
            del kwargs['tournament']

        super(RegistrationForm, self).__init__(*kargs, **kwargs)

        self.fields['player_class'].choices = (('','--'),)

        if self.tournament.registration_stages:
            stage = self.tournament.get_registration_stage()

            if stage:
                self.fields['player_class'].choices += [
                    (c.player_class.id, '%s - requires %s rating' % (
                        c.player_class.name, c.rating_required)
                    ) for c in stage.registrationstageclass_set.all()]
        else:
            self.fields['player_class'].choices += [
                (c.id, c.name) for c in self.tournament.classes.all()]

    def save(self, *kargs, **kwargs):
        player = super(RegistrationForm, self).save(*kwargs, **kwargs)

        player_class = PlayerClass.objects.get(
            id=self.cleaned_data['player_class'])

        tp = TournamentPlayer.objects.create(
            tournament=self.tournament,
            player=player,
            player_class=player_class,
            registered=datetime.now())
