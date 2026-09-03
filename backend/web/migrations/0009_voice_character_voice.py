import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def create_default_voice(apps, schema_editor):
    Voice = apps.get_model('web', 'Voice')
    Voice.objects.get_or_create(
        voice_id='longanyang',
        defaults={'name': '默认音色'},
    )


class Migration(migrations.Migration):
    dependencies = [('web', '0008_systemprompt')]

    operations = [
        migrations.CreateModel(
            name='Voice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('voice_id', models.CharField(max_length=100, unique=True)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.AddField(
            model_name='character',
            name='voice',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.voice'),
        ),
        migrations.RunPython(create_default_voice, migrations.RunPython.noop),
    ]
