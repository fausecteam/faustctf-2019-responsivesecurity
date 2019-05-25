from app import app, storage
from storage import cleanup

with app.app_context():
    cleanup()
