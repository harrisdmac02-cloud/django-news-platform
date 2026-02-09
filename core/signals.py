# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mass_mail
from django.conf import settings

from .models import Article

@receiver(post_save, sender=Article)
def notify_and_tweet_on_publish(sender, instance, created, **kwargs):
    """Send notifications only on first publish (defensive flag prevents duplicates)."""
    if created or instance.status != 'published' or instance.notifications_sent:
        return

    # Email notifications (defensive)
    recipients = set()
    if instance.publisher:
        recipients.update(instance.publisher.subscribed_readers.all())
    if instance.author and instance.author.is_journalist:
        recipients.update(instance.author.journalist_followers.all())

    if recipients and settings.EMAIL_HOST:  # Check config defensively
        subject = f"New Article: {instance.title}"
        message = (
            f"New article '{instance.title}' by {instance.author.get_full_name() or instance.author.username}.\n\n"
            f"Read here: {settings.SITE_URL}{instance.get_absolute_url()}\n\n"
            f"Best,\nNews Platform"
        )
        emails = [(subject, message, settings.DEFAULT_FROM_EMAIL, [u.email]) for u in recipients if u.email]
        try:
            send_mass_mail(emails, fail_silently=False)
        except Exception as e:
            print(f"Email notification failed: {e}")

    # Tweet removed (auth broken); set flag
    instance.notifications_sent = True
    instance.save(update_fields=['notifications_sent'])