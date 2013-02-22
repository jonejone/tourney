from django import forms
from django.core.urlresolvers import reverse
from django.core import management
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from datetime import datetime

from .models import (Player,
                     PlayerClass,
                     TournamentPlayer,
                     TournamentNewsItem,
                     TournamentOption,
                     TournamentPage,)


class TournamentNewsItemForm(forms.ModelForm):
    def __init__(self, *kargs, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))
        self.helper.form_class = 'edit-page-form'

        if kwargs.get('instance'):
            self.helper.form_action = reverse(
                'tournament-news-edit', args=[
                kwargs.get('instance').slug])
        else:
            self.helper.form_action = reverse(
                'tournament-news-create')

        super(TournamentNewsItemForm, self).__init__(*kargs, **kwargs)

    class Meta:
        model = TournamentNewsItem
        fields = ('title', 'introduction', 'body', 'is_published',)


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
    options = forms.MultipleChoiceField(
        widget=forms.widgets.CheckboxSelectMultiple,
        required=False)

    pdga_terms = forms.BooleanField(
        label='Approve PDGA terms',
        help_text='You must approve the PDGA terms' +
                  'to register for this tournament.')

    class Meta:
        model = Player
        fields = ('player_class', 'pdga_number', 'pdga_terms',
                  'name', 'country', 'email', 'phonenumber')

    def __init__(self, *kargs, **kwargs):

        if kwargs.get('tournament'):
            self.tournament = kwargs.get('tournament')
            del kwargs['tournament']

        # If there actually are no choices for the "options" field
        # for this tournament, we just remove the field from the form
        if not self.tournament.tournamentoption_set.count():
            if 'options' in self.base_fields.keys():
                del self.base_fields['options']

        # Each tournament has a setting to toggle the PDGA terms field,
        # so we must remove the field if it is turned off
        if not self.tournament.pdga_rules_approval:
            if 'pdga_terms' in self.base_fields.keys():
                del self.base_fields['pdga_terms']

        super(RegistrationForm, self).__init__(*kargs, **kwargs)

        # Take care of choices for "options" field
        if 'options' in self.fields.keys():
            option_choices = []
            for o in self.tournament.tournamentoption_set.all():
                label = '%s - %d %s' % (o.name, o.price,
                                        self.tournament.currency)

                option_choices.append((o.id, label))

            self.fields['options'].choices = option_choices

        # Take care of choices for player class
        self.fields['player_class'].choices = (('', '--'), )

        if self.tournament.registration_stages:
            stage = self.tournament.get_registration_stage()

            if stage:
                rating = '%s - requires %s rating - %s'
                self.fields['player_class'].choices += [
                    (c.player_class.id, rating % (
                        c.player_class.name,
                        c.rating_required,
                        c.get_class_price())
                    )
                for c in stage.registrationstageclass_set.all()]
        else:
            self.fields['player_class'].choices += [
                (c.id, '%s - %s' % (
                    c.name,
                    c.get_class_price(self.tournament))
                ) for c in self.tournament.classes.all()]

    def save(self, *kargs, **kwargs):
        player = super(RegistrationForm, self).save(*kwargs, **kwargs)

        player_class = PlayerClass.objects.get(
            id=self.cleaned_data['player_class'])

        tp = TournamentPlayer.objects.create(
            tournament=self.tournament,
            player=player,
            player_class=player_class,
            registered=datetime.now())

        if self.tournament.is_registration_full():
            tp.is_waiting_list = True
            tp.save()
        else:
            tp.send_registration_email()

        # TournamentPlayer saved, lets save options
        if 'options' in self.fields.keys():
            options = []
            for option_id in self.cleaned_data['options']:
                try:
                    option = self.tournament.tournamentoption_set.get(
                        id=option_id)
                except TournamentOption.DoesNotExist:
                    pass
                else:
                    options.append(option)

            tp.options = options

        if tp.player.pdga_number:
            # Run management command to update rank
            management.call_command('pdgarank', tp.player.id)
