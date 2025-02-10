from ninja import NinjaAPI
from .routers import router
import sys

is_testing = 'test' in sys.argv
api = NinjaAPI(
    version='1.0.0',
    urls_namespace='inventory_api',
    docs_url="/docs",  # This enables Swagger UI at /api/docs
    title="Inventory API",
    description="API for managing repair shop inventory and components",
)
api.add_router('', router)