from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Game, UserGameJournal

def validate_uci_move(value):
    # UCI format is either 4 characters (e.g., e2e4) or 5 characters for promotions (e.g., e7e8q)
    if len(value) not in [4, 5] or not value[0] in 'abcdefgh' or not value[1] in '12345678' or not value[2] in 'abcdefgh' or not value[3] in '12345678':
        raise ValidationError(f'Invalid UCI move format: "{value}".')

class ChessMoveForm(forms.Form):
    uci_move = forms.CharField(
        max_length=5,  # Maximum length 5 (for promotions like e7e8q)
        validators=[validate_uci_move],
        widget=forms.TextInput(attrs={'placeholder': 'Move (e.g., e2e4, e7e8q)'}),
        required=False  # Make this field optional to prevent form submission issues on resign
    )

    def clean(self):
        cleaned_data = super().clean()
        uci_move = cleaned_data.get("uci_move")
        if 'move' in self.data:  # Only validate if the "Move" button was clicked
            if not uci_move:
                raise ValidationError('You must enter a move.')
        return cleaned_data

class JoinForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label="Confirm Password")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())

class ChallengeForm(forms.Form):
    opponent = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True))

class GameDescriptionForm(forms.ModelForm):
    class Meta:
        model = UserGameJournal
        fields = ['description', 'journal_entry']  # Allow editing both fields

        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Enter a brief description', 'class': 'form-control'}),
            'journal_entry': forms.Textarea(attrs={'placeholder': 'Write detailed notes about the game', 'rows': 5, 'class': 'form-control'}),
        }
