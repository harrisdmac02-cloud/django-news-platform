# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import Article, CustomUser, Newsletter


class SignUpForm(UserCreationForm):
    """
    User registration form with mandatory role selection.

    Features:
    - Requires selection of exactly one primary role: Reader, Journalist, or Editor
    - Automatically assigns the user to the corresponding Django Group
    - Enforces single-role membership by removing any other role groups
    - Email is optional (can be useful for password reset, notifications)

    Usage:
    - Used in registration views
    - Role is presented as radio buttons
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
        """
         Save the user and assign them to the selected role group.

        - Creates the group if it doesn't exist
        - Removes membership from all other role groups (enforces single role)
        """
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
    Form used by journalists and editors to create or update articles.

    Handles:
    - Main article fields (title, slug, content, excerpt, publisher)
    - Rich textarea widgets for content and excerpt
    - Slug validation (currently minimal — consider adding uniqueness check)

    Notes:
    - Status and author are typically set in the view (not exposed here)
    - Publisher is optional (allows independent/journalist-only articles)
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
        """
        Validate the slug field.

        Current implementation is minimal.
        Consider adding:
        - Uniqueness check per author/publisher
        - Auto-generation fallback in view/model if empty
        """
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Optional: auto-generate slug in view or model save()
            pass
        return slug


class ArticleApprovalForm(forms.ModelForm):
    """
    Form used exclusively by editors to review and set the status of an article.

    - Only exposes the 'status' field
    - Uses the article's STATUS_CHOICES for the dropdown
    - Typically rendered in an approval/review interface
    - Does not allow changing content, title, etc.
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