from django.conf import settings


def debug(context):
    """
    Добавляет переменную DEBUG в контекст шаблона.
    """
    return {"DEBUG": settings.DEBUG}
