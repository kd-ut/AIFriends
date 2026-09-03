from django.db import migrations


VOICE_PRESETS = [
    ('冷静黑客·夜雾', 'longyingjing_v3'),
    ('温柔网行者·星遥', 'longyingling_v3'),
    ('灵动技术少女·玲', 'longanling_v3'),
    ('利落佣兵少女·凛', 'longanli_v3'),
    ('磁性战术顾问·天曜', 'longtian_v3'),
    ('清爽街头青年·疾风', 'longanlang_v3'),
]


def add_voice_presets(apps, schema_editor):
    Voice = apps.get_model('web', 'Voice')
    Voice.objects.filter(voice_id='longanyang').update(name='阳光行动派·曜')
    for name, voice_id in VOICE_PRESETS:
        Voice.objects.update_or_create(
            voice_id=voice_id,
            defaults={'name': name},
        )


def remove_voice_presets(apps, schema_editor):
    Voice = apps.get_model('web', 'Voice')
    Voice.objects.filter(voice_id__in=[item[1] for item in VOICE_PRESETS]).delete()
    Voice.objects.filter(voice_id='longanyang').update(name='默认音色')


class Migration(migrations.Migration):
    dependencies = [('web', '0009_voice_character_voice')]

    operations = [
        migrations.RunPython(add_voice_presets, remove_voice_presets),
    ]
