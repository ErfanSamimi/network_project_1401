from django import forms


class LoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}),
        required=True
    )
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        required=True
    )
