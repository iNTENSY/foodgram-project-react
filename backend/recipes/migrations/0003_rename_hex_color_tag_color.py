# Generated by Django 3.2.3 on 2024-02-13 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tag',
            old_name='hex_color',
            new_name='color',
        ),
    ]
