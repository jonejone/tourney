# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Tournament.is_couples_tourney'
        db.add_column(u'tournament_tournament', 'is_couples_tourney',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Tournament.is_couples_tourney'
        db.delete_column(u'tournament_tournament', 'is_couples_tourney')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'tournament.player': {
            'Meta': {'object_name': 'Player'},
            'club': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'pdga_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pdga_rating': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'phonenumber': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'tournament.playerclass': {
            'Meta': {'object_name': 'PlayerClass'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        u'tournament.registrationstage': {
            'Meta': {'object_name': 'RegistrationStage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opens': ('django.db.models.fields.DateTimeField', [], {}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"})
        },
        u'tournament.registrationstageclass': {
            'Meta': {'object_name': 'RegistrationStageClass'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player_class': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.PlayerClass']"}),
            'rating_required': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'registration_stage': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.RegistrationStage']"})
        },
        u'tournament.tournament': {
            'Meta': {'object_name': 'Tournament'},
            'classes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['tournament.PlayerClass']", 'symmetrical': 'False'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'google_analytics_account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'header_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_couples_tourney': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5'}),
            'max_players': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '72'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'payment_information': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pdga_rules_approval': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'registration_ends': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'registration_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'registration_opens': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'registration_stages': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'tournament_admin_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'wildcard_spots': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        u'tournament.tournamentadmin': {
            'Meta': {'object_name': 'TournamentAdmin'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'tournament.tournamentclassprice': {
            'Meta': {'object_name': 'TournamentClassPrice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player_class': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.PlayerClass']"}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"})
        },
        u'tournament.tournamentnewsitem': {
            'Meta': {'ordering': "['-created']", 'object_name': 'TournamentNewsItem'},
            'body': ('ckeditor.fields.RichTextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduction': ('ckeditor.fields.RichTextField', [], {}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'tournament.tournamentoption': {
            'Meta': {'object_name': 'TournamentOption'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"})
        },
        u'tournament.tournamentpage': {
            'Meta': {'ordering': "['navigation_position']", 'object_name': 'TournamentPage'},
            'body': ('ckeditor.fields.RichTextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'navigation_position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'show_in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"})
        },
        u'tournament.tournamentplayer': {
            'Meta': {'ordering': "['player_class', '-player__pdga_rating']", 'object_name': 'TournamentPlayer'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_waiting_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'options': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['tournament.TournamentOption']", 'symmetrical': 'False', 'blank': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Player']"}),
            'player_class': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.PlayerClass']"}),
            'registered': ('django.db.models.fields.DateTimeField', [], {}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"})
        },
        u'tournament.tournamentsite': {
            'Meta': {'object_name': 'TournamentSite'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tournament.Tournament']"})
        }
    }

    complete_apps = ['tournament']