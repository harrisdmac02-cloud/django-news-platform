# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import Article, CustomUser, Newsletter


class SignUpForm(UserCreationForm):
    """
        Registration form with role selection.
        Assigns user to exactly one main role group: Reader / Journalist / Editor.
    """
    ROLE_CHOICES = (
        ('reader', 'Reader'),
        ('journalist', 'Journalist'),
        ('editor', 'Editor'),
    )

    # ── Better / safer way ───────────────────────────────────────
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(
            attrs={'class': 'form-check-input'}
        ),
        required=True,
        error_messages={
            'required': 'Please select your role.',
            'invalid_choice': 'Please select a valid role.'
        }
    )

    email = forms.EmailField(required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def clean_role(self):
        role = self.cleaned_data.get('role')
        valid_choices = dict(self.fields['role'].choices)
        if role not in valid_choices:
            raise forms.ValidationError(
                f"Invalid role. Choose one of: {', '.join(valid_choices.values())}"
            )
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

            role = self.cleaned_data['role']
            group_name = role.capitalize()  # 'Reader', 'Journalist', 'Editor'
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

            # Enforce single role: remove all other role groups this user is in
            other_roles = {'Reader', 'Journalist', 'Editor'} - {group_name}
            for other_group_name in other_roles:
                try:
                    other_group = Group.objects.get(name=other_group_name)
                    user.groups.remove(other_group)
                except Group.DoesNotExist:
                    pass  # group didn't exist → nothing to remove

        return user

class ArticleForm(forms.ModelForm):
    """
    Form for creating / updating articles.
    Journalists and editors use this.
    """
    class Meta:
        model = Article
        fields = ['title', 'slug', 'content', 'excerpt', 'publisher']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 14, 'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Optional: auto-generate slug in view or model save()
            pass
        return slug


class ArticleApprovalForm(forms.ModelForm):
    """
    Simple form used by editors to approve/reject/ change status.
    """
    class Meta:
        model = Article
        fields = ['status']
        widgets = {
            'status': forms.Select(
                choices=Article.STATUS_CHOICES,
                attrs={'class': 'form-select form-select-lg'}
            )
        }


class NewsletterForm(forms.ModelForm):
    """
    Form for journalists to create / update newsletters.
    Similar structure to ArticleForm.
    """
    class Meta:
        model = Newsletter
        fields = ['title', 'slug', 'content', 'excerpt', 'publisher']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 16, 'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.Select(attrs={'class': 'form-select'}),
        }