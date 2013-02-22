from datetime import datetime, date

from django.template.loader import get_template
from django.template import Context
from django.core.mail import send_mail
from django_countries import CountryField
from django.utils.timezone import utc
from django.utils import simplejson
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

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
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    user = models.ForeignKey(User)
    classes = models.ManyToManyField(PlayerClass)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    registration_stages = models.BooleanField(
        default=False)

    registration_opens = models.DateTimeField(
        blank=True, null=True)

    registration_ends = models.DateTimeField(
        blank=True, null=True)

    payment_information = models.TextField(
        blank=True, null=True)

    tournament_admin_email = models.EmailField(
        blank=True, null=True)

    currency = models.CharField(
        max_length=3, blank=True, null=True)

    header_image = models.ImageField(
        upload_to='tournament-headers/', blank=True, null=True)

    google_analytics_account = models.CharField(
        blank=True, null=True, max_length=30)

    pdga_rules_approval = models.BooleanField(
        default=0)

    max_players = models.PositiveSmallIntegerField(
        default=72)

    wildcard_spots = models.PositiveSmallIntegerField(
        default=0)

    def get_available_spots(self):
        players = self.tournamentplayer_set.count()
        return self.max_players - self.wildcard_spots - players

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
        if self.get_available_spots() > 0:
            return False

        return True

    def __unicode__(self):
        return self.name


class Player(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)

    pdga_number = models.PositiveIntegerField(
        verbose_name='PDGA Number',
        blank=True,
        null=True)

    user = models.ForeignKey(
        User, blank=True, null=True)

    phonenumber = models.CharField(
        max_length=20, blank=True, null=True)

    pdga_rating = models.PositiveSmallIntegerField(
        blank=True, null=True)

    country = CountryField()

    def __unicode__(self):
        return self.name


class TournamentOption(models.Model):
    tournament = models.ForeignKey(Tournament)
    name = models.CharField(max_length=50)
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


class TournamentPlayer(models.Model):
    player = models.ForeignKey(Player)
    player_class = models.ForeignKey(PlayerClass)
    tournament = models.ForeignKey(Tournament)
    registered = models.DateTimeField()
    is_paid = models.BooleanField()
    options = models.ManyToManyField(TournamentOption)
    is_waiting_list = models.BooleanField(default=0)

    class Meta:
        ordering = ['player_class', '-player__pdga_rating', ]

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

        send_mail(
            subject,
            email_body,
            self.tournament.tournament_admin_email,
            [self.player.email, self.tournament.tournament_admin_email])


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
