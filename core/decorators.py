# core/decorators.py
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def journalist_required(view_func):
    """
    Decorator that restricts access to views to users who are journalists.

    This decorator:
    - Requires the user to be logged in (combines with @login_required)
    - Checks if the user has the 'is_journalist' property set to True
    - Redirects non-journalists to the home page with an error message

    Usage:
        @journalist_required
        def create_article(request):
            ...

    Args:
        view_func: The view function to decorate.

    Returns:
        function: The wrapped view function.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request.user, 'is_journalist', False):
            messages.error(request, "Only journalists can perform this action.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def editor_required(view_func):
    """
    Decorator that restricts access to views to users who are editors.

    This decorator:
    - Requires the user to be logged in (combines with @login_required)
    - Checks if the user has the 'is_editor' property set to True
    - Redirects non-editors to the home page with an error message

    Usage:
        @editor_required
        def approve_article(request, pk):
            ...

    Args:
        view_func: The view function to decorate.

    Returns:
        function: The wrapped view function.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request.user, 'is_editor', False):
            messages.error(request, "Only editors can perform this action.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view