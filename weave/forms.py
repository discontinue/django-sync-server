'''
Forms used by weave.
FIXME: Not complete yet.

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Jens Diemer
'''

from django import forms

class ChangePasswordForm(forms.Form):
    uid = forms.CharField(max_length='30')
    password = forms.CharField(max_length='128')
    new = forms.CharField(max_length='128')
