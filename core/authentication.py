# core/authentication.py

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import ApiClient


class ApiKeyAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class that authenticates requests using an API key.

    Supports providing the key in two ways:
      - HTTP header: `X-API-Key: <your-key>`
      - Query parameter: `?api_key=<your-key>`

    Behavior:
      - If no key is provided → authentication is skipped (returns None)
      - If key is provided → looks up an active ApiClient with matching key
      - On success → updates the `last_used_at` timestamp and attaches the linked user
      - On failure → raises AuthenticationFailed (401 response)

    This authentication is typically used for third-party applications or API clients
    that inherit subscription access from a linked reader account.
    """

    def authenticate(self, request):
        """
        Attempt to authenticate the request using an API key.

        Looks for the key in the `X-API-Key` header first, then falls back to
        the `api_key` query parameter.

        Args:
            request: The current request object

        Returns:
            tuple: (user, authenticator) on successful authentication
            None: if no credentials were provided (authentication not attempted)

        Raises:
            AuthenticationFailed: if the provided key is invalid or the client is inactive
        """
        api_key = (
            request.headers.get('X-API-Key') or
            request.query_params.get('api_key')
        )
        if not api_key:
            return None

        try:
            client = ApiClient.objects.select_related('user').get(
                api_key=api_key,
                is_active=True
            )
            client.last_used_at = timezone.now()
            client.save(update_fields=['last_used_at'])
            return (client.user, client)  # user, auth instance
        except ApiClient.DoesNotExist:
            raise AuthenticationFailed(
                'Invalid or inactive API key',
                code='invalid_api_key'
            )