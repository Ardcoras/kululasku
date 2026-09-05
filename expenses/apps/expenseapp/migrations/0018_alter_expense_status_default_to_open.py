# Generated migration: revert Expense.status default from -1 (draft) back to 0 (open).
# The pool_bundle_view now sets status=-1 explicitly when creating a draft,
# so the model default no longer needs to be -1.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenseapp', '0017_alter_expenseline_organisation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='status',
            field=models.IntegerField(
                choices=[(-1, 'Draft'), (0, 'Open'), (1, 'Sent')],
                default=0,
                verbose_name='Status',
            ),
        ),
    ]
