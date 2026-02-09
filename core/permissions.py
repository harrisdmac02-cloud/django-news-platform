# core/permissions.py
from rest_framework import permissions


class IsApiClientForSubscribedContent(permissions.BasePermission):
    """
    Allows access only if the request comes from a valid ApiClient
    and the content matches the linked user's subscriptions.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'api_clients')  # rough check that it's an ApiClient user

    def has_object_permission(self, request, view, obj):
        # For single object retrieval (if needed later)
        if hasattr(obj, 'publisher') and obj.publisher:
            return request.user.subscribed_publishers.filter(pk=obj.publisher.pk).exists()
        if hasattr(obj, 'author') and obj.author.is_journalist:
            return request.user.subscribed_journalists.filter(pk=obj.author.pk).exists()
        return False