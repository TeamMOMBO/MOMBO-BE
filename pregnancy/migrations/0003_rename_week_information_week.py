# Generated by Django 5.1.2 on 2024-11-06 10:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pregnancy', '0002_alter_faq_answer_alter_faq_question_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='information',
            old_name='Week',
            new_name='week',
        ),
    ]