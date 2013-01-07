from django.forms import ModelForm

from .models import Player 

class RegistrationForm(ModelForm):
    class Meta:
        model = Player
        fields = (
            'pdga_number', 'name', 'email',
            'phonenumber')
