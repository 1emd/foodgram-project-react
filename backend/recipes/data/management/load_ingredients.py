import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                name, description = row
                Ingredient.objects.create(name=name, description=description)
                self.stdout.write(self.style.SUCCESS(
                    f'Ингредиент успешно загружен: {name}'))
