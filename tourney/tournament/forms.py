from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django import forms
from django.core.urlresolvers import reverse
from django.core import management
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from datetime import datetime

from .models import (Player,
                     PlayerClass,
                     Tournament,
                     TournamentPlayer,
                     TournamentNewsItem,
                     TournamentOption,
                     TournamentPage,)

from django.core.mail import send_mass_mail

class EmailPlayersForm(forms.Form):

    email_player_list = forms.BooleanField(
        required=False,
        initial=True)

    email_waiting_list = forms.BooleanField(
        required=False,
        initial=True)

    subject = forms.CharField()

    body = forms.CharField(
        widget=forms.Textarea()
    )

    sender = forms.CharField()

    def get_emails(self, tournament, player_list, waiting_list):
        if not player_list and not waiting_list:
            return []

        emails = []

        if waiting_list:
            for player in tournament.get_waiting_list():
                if player.player.email:
                    emails.append(player.player.email)

        if player_list:
            for player in tournament.get_player_list():
                if player.player.email:
                    emails.append(player.player.email)

        return emails

    def save(self, tournament):

        messages = []
        recipients = self.get_emails(
            tournament,
            self.cleaned_data['email_player_list'],
            self.cleaned_data['email_waiting_list'])

        for recipient in recipients:

            messages.append((
                self.cleaned_data['subject'],
                self.cleaned_data['body'],
                self.cleaned_data['sender'],
                [recipient,]))

        send_mass_mail(messages)


class TournamentPlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        exclude = ('user',)


class TournamentRegistrationForm(forms.ModelForm):
    class Meta:
        model = TournamentPlayer
        exclude = ('tournament', 'player')


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        exclude = (
            'slug', 'user', 'registration_stages',)


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
            'pdga_number', 'name', 'club', 'email',
            'phonenumber')


class RegistrationForm(PlayerForm):
    player_class = forms.ChoiceField(
        label=_('Player class'))

    options = forms.MultipleChoiceField(
        label=_('Options'),
        widget=forms.widgets.CheckboxSelectMultiple,
        required=False)

    pdga_terms = forms.BooleanField(
        label=_('Approve PDGA terms'),
        help_text=_('You must approve the PDGA terms' +
                  'to register for this tournament.'))

    is_reserved_player = forms.BooleanField(
        label=_('Reserved player'),
        help_text=_('I am granted a reserved spot based on last years results.'),
        required=False)

    class Meta:
        model = Player
        fields = ('player_class', 'is_reserved_player', 'pdga_number', 'pdga_terms',
                  'name', 'club', 'country', 'email', 'phonenumber', 'options')

    def __init__(self, *kargs, **kwargs):

        if 'tournament' in kwargs:
            self.tournament = kwargs['tournament']
            del kwargs['tournament']

        super(RegistrationForm, self).__init__(*kargs, **kwargs)

        # Set default country to Norway since all tourneys
        # so far have been in Norway.
        self.fields['country'].initial = 'NO'

        # If there actually are no choices for the "options" field
        # for this tournament, we just remove the field from the form
        if self.tournament.tournamentoption_set.count() == 0:
            del self.fields['options']

        # Each tournament has a setting to toggle the PDGA terms field,
        # so we must remove the field if it is turned off
        if not self.tournament.pdga_rules_approval:
            del self.fields['pdga_terms']

        # Take care of choices for "options" field
        if 'options' in self.fields.keys():
            option_choices = []
            for o in self.tournament.tournamentoption_set.filter(
                is_available=True):

                label = '%s - %d %s' % (o.name, o.price,
                                        self.tournament.currency)

                option_choices.append((o.id, label))

            self.fields['options'].choices = option_choices

        # Take care of choices for player class
        self.fields['player_class'].choices = (('', '--'), )

        # Make some changes for couples tourneys
        if self.tournament.is_couples_tourney:
            # Remove PDGA field if couples tourney
            del self.fields['pdga_number']

            # Change labels
            self.fields['name'].label = _('Name player 1 / player 2')
            self.fields['club'].label = _('Club player 1 / player 2')

        if self.tournament.registration_stages:
            stage = self.tournament.get_registration_stage()

            if stage:
                rating = '%s - %s'
                self.fields['player_class'].choices += [
                    (c.player_class.id, rating % (
                        c.player_class.name,
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


        tp_kwargs = {
            'tournament': self.tournament,
            'player': player,
            'player_class': player_class,
            'registered': now(),
        }

        # Create TournamentPlayer
        tp = TournamentPlayer.objects.create(**tp_kwargs)

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

        return tp
