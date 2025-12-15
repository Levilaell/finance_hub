# Generated migration for acquisition_angle field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_add_user_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='acquisition_angle',
            field=models.CharField(
                blank=True,
                help_text='Ângulo/campanha de aquisição (ex: time, price, delay, visibility)',
                max_length=50,
                null=True,
                verbose_name='acquisition angle'
            ),
        ),
    ]
