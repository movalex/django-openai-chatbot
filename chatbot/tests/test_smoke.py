from django.conf import settings


def test_settings_loaded():
    # Basic sanity checks that do not require database or external services
    assert hasattr(settings, "BASE_DIR")
    assert settings.STATIC_URL == "/static/"
    # DEBUG is read from env; ensure it's a boolean
    assert isinstance(settings.DEBUG, bool)
