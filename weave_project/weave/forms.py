
from django import forms

class ChangePasswordForm(forms.Form):
    username = forms.CharField(max_length='30')
    password = forms.CharField(max_length='128')
    new = forms.CharField(max_length='128')