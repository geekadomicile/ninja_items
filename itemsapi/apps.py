from django.apps import AppConfig


class ItemsApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'itemsapi'
    
    def ready(self):
        # Prevent multiple registrations during testing
        if not hasattr(self, 'registered'):
            self.registered = True
            # Your registration code here
