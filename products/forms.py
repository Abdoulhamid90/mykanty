from django import forms
from .models import Product, ProductImage, Review, Category

class ProductForm(forms.ModelForm):
    """
    Formulaire pour ajouter/modifier un produit
    """
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'condition',
            'price', 'discount_price', 'stock_quantity',
            'main_image', 'brand', 'sku', 'weight',
            'is_active', 'is_featured'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom du produit'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Description détaillée du produit...'
            }),
            'condition': forms.Select(attrs={
                'class': 'form-select',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Prix en XOF',
                'step': '0.01'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Prix promotionnel (optionnel)',
                'step': '0.01'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Quantité en stock'
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Marque (optionnel)'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Référence produit (optionnel)'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Poids en kg (optionnel)',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        labels = {
            'is_active': 'Activer ce produit',
            'is_featured': 'Mettre en avant',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs optionnels visuellement
        self.fields['discount_price'].required = False
        self.fields['brand'].required = False
        self.fields['sku'].required = False
        self.fields['weight'].required = False


class ProductImageForm(forms.ModelForm):
    """
    Formulaire pour ajouter des images supplémentaires
    """
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Description de l\'image (optionnel)'
            }),
        }


class ReviewForm(forms.ModelForm):
    """
    Formulaire pour laisser un avis
    """
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'guest_name', 'guest_email']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Partagez votre expérience avec ce produit...'
            }),
            'guest_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom (si non connecté)'
            }),
            'guest_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre email (si non connecté)'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si l'utilisateur est connecté, cacher les champs invité
        if user and user.is_authenticated:
            self.fields['guest_name'].widget = forms.HiddenInput()
            self.fields['guest_email'].widget = forms.HiddenInput()
            self.fields['guest_name'].required = False
            self.fields['guest_email'].required = False


class ProductSearchForm(forms.Form):
    """
    Formulaire de recherche de produits
    """
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'placeholder': 'Rechercher un produit...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='Toutes les catégories',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Prix min'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Prix max'
        })
    )
    condition = forms.ChoiceField(
        choices=[('', 'Tous')] + Product.CONDITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    in_stock = forms.BooleanField(
        required=False,
        label='En stock uniquement',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )
