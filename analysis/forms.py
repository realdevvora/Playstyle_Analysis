from django import forms
from django.contrib.auth.models import User

class ChampForm(forms.Form):
    champion = forms.CharField(label='Your name', max_length=100)
    class Meta:
        model = User
        fields = ['champion']