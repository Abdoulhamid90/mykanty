from django import forms
from .models import User, SellerProfile, SellerRequest


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirmer le mot de passe')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'city', 'country']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone_number', 'city', 'country', 'profile_picture']


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['business_name', 'business_description', 'business_logo']


class SellerRequestForm(forms.ModelForm):
    class Meta:
        model = SellerRequest
        fields = [
            'full_name',
            'contact_number',
            'whatsapp_number',
            'location',
            'preferred_payment_method',
            'product_types',
            'business_description',
            'id_document',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Kofi Mensah'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: +228 90 00 00 00'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: +228 90 00 00 00'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Lomé, Tokoin'
            }),
            'preferred_payment_method': forms.Select(attrs={
                'class': 'form-input'
            }),
            'product_types': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Vêtements, chaussures, accessoires'
            }),
            'business_description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Décrivez votre activité...'
            }),
            'id_document': forms.FileInput(attrs={
                'class': 'form-input'
            }),
        }