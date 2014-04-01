from datetime import datetime, date

from django.utils.translation import ugettext_lazy as _
from django.template.loader import get_template
from django.template import Context
from django.core.mail import EmailMessage
from django_countries import CountryField
from django.utils.timezone import utc
from django.utils import simplejson
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.conf import settings

from ckeditor.fields import RichTextField


class PlayerClass(models.Model):
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

    def get_class_price(self, tournament):
        try:
            p = tournament.tournamentclassprice_set.get(
                player_class=self)
        except TournamentClassPrice.DoesNotExist:
            return None

        return '%d %s' % (p.price, tournament.currency)


class RegistrationStage(models.Model):
    tournament = models.ForeignKey('Tournament')
    opens = models.DateTimeField()

    def __unicode__(self):
        return u'Stage opens %s for tournament %s' % (
            self.opens, self.tournament.name)


class RegistrationStageClass(models.Model):
    registration_stage = models.ForeignKey(RegistrationStage)
    player_class = models.ForeignKey(PlayerClass)
    rating_required = models.PositiveSmallIntegerField()

    def get_class_price(self):
        tournament = self.registration_stage.tournament
        try:
            p = tournament.tournamentclassprice_set.get(
                player_class=self.player_class)
        except TournamentClassPrice.DoesNotExist:
            return None

        return '%d %s' % (p.price, tournament.currency)


class Tournament(models.Model):

    name = models.CharField(
        _('Name'),
        max_length=100)

    slug = models.SlugField()
    user = models.ForeignKey(User)

    classes = models.ManyToManyField(
        PlayerClass, help_text=_('Classes'))

    language = models.CharField(
        _('Language'),
        max_length=5,
        default='en',
        choices=settings.LANGUAGES)

    start_date = models.DateField(
        _('Start date'))

    end_date = models.DateField(
        _('End date'), blank=True, null=True)

    registration_stages = models.BooleanField(
        _('Registration stages'),
        default=False)

    registration_opens = models.DateTimeField(
        _('Registration opens'),
        blank=True, null=True)

    registration_ends = models.DateTimeField(
        _('Registration ends'),
        blank=True, null=True)

    payment_information = models.TextField(
        _('Payment information'),
        blank=True, null=True)

    tournament_admin_email = models.EmailField(
        _('Admin email address'),
        blank=True, null=True)

    currency = models.CharField(
        _('Currency'),
        max_length=3, blank=True, null=True)

    header_image = models.ImageField(
        _('Header image'),
        upload_to='tournament-headers/', blank=True, null=True)

    google_analytics_account = models.CharField(
        _('Google Analytics account'),
        blank=True, null=True, max_length=30)

    pdga_rules_approval = models.BooleanField(
        _('Require PDGA rules approval'),
        default=0)

    max_players = models.PositiveSmallIntegerField(
        _('Max players'),
        default=72)

    wildcard_spots = models.PositiveSmallIntegerField(
        _('Wildcard spots'),
        default=0)

    @property
    def language_code(self):
        if self.id == 1:
            return 'en'
        else:
            return 'no'

    def get_available_spots(self):
        players = self.tournamentplayer_set.filter(
            is_waiting_list=False).count()
        return self.max_players - self.wildcard_spots - players

    def get_player_list(self):
        return self.tournamentplayer_set.filter(
            is_waiting_list=False)

    def get_player_list_email_count(self):
        return self.get_player_list().filter(
            player__email__isnull=False).exclude(
                player__email='').count()

    def get_player_list_count(self):
        return self.get_player_list().count()

    def get_waiting_list(self):
        return self.tournamentplayer_set.filter(
            is_waiting_list=True)

    def get_waiting_list_count(self):
        return self.get_waiting_list().count()

    def get_waiting_list_email_count(self):
        return self.get_waiting_list().filter(
            player__email__isnull=False).exclude(
                player__email='').count()

    def get_url(self):
        try:
            ts = self.tournamentsite_set.all()[0]
        except IndexError:
            return None

        return 'http://%s/' % ts.site.domain

    def get_stages_json(self):
        current = self.get_registration_stage()
        stages = []

        for stage in self.registrationstage_set.all():
            stage_dict = {
                'id': stage.id,
                'is_current': False,
                'classes': [{
                    'rating_required': c.rating_required,
                    'class_id': c.player_class.id
                } for c in stage.registrationstageclass_set.all()]
            }

            if stage == current:
                stage_dict.update({
                    'is_current': True})

            stages.append(stage_dict)

        return simplejson.dumps(stages)

    def is_registration_open(self):
        if self.registration_stages:
            current = self.get_registration_stage()
            if not current:
                return False

            return True
        else:
            now = datetime.utcnow().replace(tzinfo=utc)

            if now > self.registration_opens and \
                    now < self.registration_ends:

                return True

            return False

    def get_registration_stage(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        today = date.today()

        if not self.registration_stages:
            return None

        current_stage = None

        for stage in self.registrationstage_set.all():
            if stage.opens <= now and today <= self.start_date:
                current_stage = stage

        return current_stage

    def is_registration_finished(self):
        now = datetime.utcnow().replace(tzinfo=utc)

        if self.registration_stages:
            pass
        else:
            if now >= self.registration_ends:
                return True

            return False

    def is_registration_full(self):
        if self.get_available_spots() > 0 and \
            self.get_waiting_list_count() < 1:

            return False

        return True

    def __unicode__(self):
        return self.name


class Player(models.Model):
    name = models.CharField(
        _('Name'),
        max_length=50)

    email = models.EmailField(
        _('Email'),
        blank=True, null=True)

    pdga_number = models.PositiveIntegerField(
        verbose_name=_('PDGA Number'),
        blank=True,
        null=True)

    user = models.ForeignKey(
        User, blank=True, null=True)

    phonenumber = models.CharField(
        _('Phonenumber'),
        max_length=20, blank=True, null=True)

    pdga_rating = models.PositiveSmallIntegerField(
        _('PDGA Rating'),
        blank=True, null=True)

    country = CountryField(
        _('Country'))

    club = models.CharField(
        _('Club'),
        max_length=100,
        blank=True,
        null=True,)

    def __unicode__(self):
        return self.name


class TournamentOption(models.Model):
    tournament = models.ForeignKey(Tournament)
    name = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)
    price = models.DecimalField(
        decimal_places=2,
        max_digits=8)

    def __unicode__(self):
        return self.name

    def get_price(self):
        return '%d %s' % (self.price, self.tournament.currency)


class TournamentClassPrice(models.Model):
    tournament = models.ForeignKey(Tournament)
    price = models.DecimalField(
        decimal_places=2,
        max_digits=8)

    player_class = models.ForeignKey(PlayerClass)


class NoTournamentSpotsException(Exception):
    pass


class TournamentPlayer(models.Model):
    player = models.ForeignKey(Player)
    player_class = models.ForeignKey(PlayerClass)
    tournament = models.ForeignKey(Tournament)
    registered = models.DateTimeField()
    is_paid = models.BooleanField()
    options = models.ManyToManyField(
        TournamentOption, blank=True)
    is_waiting_list = models.BooleanField(default=0)

    class Meta:
        ordering = ['player_class', '-player__pdga_rating', ]

    def __unicode__(self):
        return '\'%s\' in %s' % (
            self.player.name,
            self.tournament.name)

    def accept_player(self):
        if not self.is_waiting_list:
            return

        # We can't accept player if there are no spots
        if self.tournament.get_available_spots() < 1:
            raise NoTournamentSpotsException

        self.is_waiting_list = False
        self.save()
        self.send_accepted_email()
        #self.send_registration_email()

    def get_options_price(self):
        price = 0

        for option in self.options.all():
            price += option.price

        return price

    def get_player_price(self):
        return self.get_class_price() + \
            self.get_options_price()

    def get_class_price(self):
        p = self.tournament.tournamentclassprice_set.get(
            player_class=self.player_class)

        return p.price

    def send_accepted_email(self):
        subject = _('Player accepted into %s' % self.tournament.name)
        email_template = get_template(
            'tournament/accepted-email.txt')

        context = Context({
            'tournament': self.tournament,
            'player': self.player,
            'player_class': self.player_class,
            'tournament_player': self,
        })

        email_body = email_template.render(context)
        from_email = self.tournament.tournament_admin_email

        message = EmailMessage(
            subject,
            email_body,
            from_email,
            [self.player.email, from_email],
            headers = {'Reply-To': from_email})

        message.send()



    def send_registration_email(self):
        if not self.player.email:
            return

        subject = 'Registration for %s' % self.tournament.name
        email_template = get_template(
            'tournament/registration-email.txt')

        try:
            p = self.tournament.tournamentclassprice_set.get(
                player_class=self.player_class)
        except TournamentClassPrice.DoesNotExist:
            price = None
        else:
            price = p.price

        total_amount = 0

        if price:
            total_amount += price

        for option in self.options.all():
            total_amount += option.price

        context = Context({
            'tournament': self.tournament,
            'player': self.player,
            'player_class': self.player_class,
            'tournament_player': self,
            'price': '%d %s' % (price, self.tournament.currency),
            'total_amount': '%d %s' % (
                total_amount, self.tournament.currency)
        })

        email_body = email_template.render(context)
        from_email = self.tournament.tournament_admin_email

        message = EmailMessage(
            subject,
            email_body,
            from_email,
            [self.player.email, from_email],
            headers = {'Reply-To': from_email})

        message.send()


class TournamentPage(models.Model):
    tournament = models.ForeignKey(Tournament)
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    body = RichTextField()

    show_in_navigation = models.BooleanField(
        default=True)

    navigation_position = models.PositiveSmallIntegerField(
        blank=True, null=True)

    class Meta:
        ordering = ['navigation_position', ]

    def __unicode__(self):
        return self.title


class TournamentNewsItem(models.Model):
    tournament = models.ForeignKey(Tournament)
    user = models.ForeignKey(User)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    introduction = RichTextField()
    body = RichTextField()
    created = models.DateTimeField()
    published = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created', ]

    def __unicode__(self):
        return self.title


class TournamentSite(models.Model):
    tournament = models.ForeignKey(Tournament)
    site = models.ForeignKey(Site)


class TournamentAdmin(models.Model):
    tournament = models.ForeignKey(Tournament)
    user = models.ForeignKey(User)
