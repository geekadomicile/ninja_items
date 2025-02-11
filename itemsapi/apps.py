from django.apps import AppConfig


class ItemsApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'itemsapi'
    
    def ready(self):
        import itemsapi.signals 
        
