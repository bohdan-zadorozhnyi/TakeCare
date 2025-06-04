from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"
    
    def ready(self):
        """
        Register signals when the app is ready
        """
        import notifications.signals  # Import signals to register them
        notifications.signals.ready()  # Call the ready function to register signals
