# Generated by Django 3.2.13 on 2022-11-06 20:48

from django.db import migrations, models
import expenseapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('expenseapp', '0012_workflow_organisation'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_fi', models.CharField(blank=True, max_length=200, verbose_name='Otsikko')),
                ('description_fi', models.TextField(blank=True, max_length=2000, verbose_name='Selite')),
                ('title_se', models.CharField(blank=True, max_length=200, verbose_name='Rubrik')),
                ('description_se', models.TextField(blank=True, max_length=2000, verbose_name='Förklaring')),
                ('title_en', models.CharField(blank=True, max_length=200, verbose_name='Title')),
                ('description_en', models.TextField(blank=True, max_length=2000, verbose_name='Content')),
                ('start_date', models.DateTimeField(blank=True, verbose_name='Näkyvissä alkaen')),
                ('end_date', models.DateTimeField(blank=True, verbose_name='Päättyy')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Sent')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Edited')),
            ],
            options={
                'verbose_name': 'Tiedoksianto',
                'verbose_name_plural': 'Tiedoksiannot',
            },
        ),
        migrations.AlterModelOptions(
            name='accountdimension',
            options={'verbose_name': 'Kustannuspaikan koodi', 'verbose_name_plural': 'Kustannuspaikat'},
        ),
        migrations.AlterModelOptions(
            name='expense',
            options={'verbose_name': 'Kululasku', 'verbose_name_plural': '  Kululaskut'},
        ),
        migrations.AlterModelOptions(
            name='organisation',
            options={'verbose_name': 'Organisaatio', 'verbose_name_plural': ' Organisaatiot'},
        ),
        migrations.AlterModelOptions(
            name='person',
            options={'verbose_name_plural': 'Henkilötiedot'},
        ),
        migrations.AlterField(
            model_name='expense',
            name='description',
            field=models.CharField(help_text='For example name of event, cost centre, activity area, or responsible employee', max_length=255, verbose_name='Allocation of cost'),
        ),
        migrations.AlterField(
            model_name='expenseline',
            name='receipt',
            field=models.FileField(blank=True, help_text='A scan or picture of the receipt. Accepted formats include PDF, PNG and JPG. Note: The receipt must clearly show what, when and how much has been paid!', null=True, upload_to='uploads/receipts', validators=[expenseapp.models.validate_file_extension], verbose_name='Receipt'),
        ),
    ]