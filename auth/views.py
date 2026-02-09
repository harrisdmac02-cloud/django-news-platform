# auth/views.py
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = 'core/login.html'  # keep using core's template (or move to auth/templates later)

    def form_valid(self, form):
        # Log the user in (this is done by parent class)
        response = super().form_valid(form)

        user = form.get_user()

        # Role-based redirect after successful login
        if hasattr(user, 'is_editor') and user.is_editor:
            return HttpResponseRedirect(reverse_lazy('core:editor_dashboard'))

        elif hasattr(user, 'is_journalist') and user.is_journalist:
            # You can change this to a journalist-specific dashboard later
            return HttpResponseRedirect(reverse_lazy('core:feed'))  # or 'core:journalist_dashboard'

        else:
            # Readers + any other roles
            return HttpResponseRedirect(reverse_lazy('core:home'))

        return response