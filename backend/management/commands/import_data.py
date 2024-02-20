import os.path

from django.core.management import BaseCommand

from foodgram.settings import BASE_DIR


class Command(BaseCommand):
    help = 'Import .csv to database'

    def handle(self, *args, **options):
        with open(os.path.join(BASE_DIR.parent, 'data/ingredient.json')) as f:
            pass
