import os

from django.conf import settings


def remove_old_photo(photo):
    default_photos = {
        'user/photos/default.png',
        'user/photos/default-avatar.png',
        'user/photos/default-anime-avatar.png',
    }
    if photo and photo.name not in default_photos:
        old_path = settings.MEDIA_ROOT / photo.name
        if os.path.exists(old_path):
            os.remove(old_path)
