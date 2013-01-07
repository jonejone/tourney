from django.test import TestCase
from django.contrib.auth.models import User

from datetime import date

from .models import Tournament, Player
from .forms import RegistrationForm

class RegisterPlayerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'foo@bar.com', 'foo')

        self.tournament = Tournament.objects.create(
            name='Some tournament',
            slug='foo',
            user=self.user,
            start_date=date.today())


    def test_post_register_player(self):
        r = self.client.post(
            '/registration/',
            {'name': 'Tester'})

        self.assertEqual(r.status_code, 302)

        self.assertEqual(
            r['location'],
            'http://testserver/registration-complete/')

        self.assertEqual(Player.objects.count(), 1)


    def test_get_register_player(self):
        r = self.client.get('/registration/')

        self.assertEqual(r.status_code, 200)
        self.assertTrue('id_pdga_number' in r.content)
