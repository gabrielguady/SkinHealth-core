import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def custom_username_validator(value):
    """
    Validador personalizado para nomes de usuário que permite letras, números,
    @/./+/-/_ caracteres, e espaços.
    """
    regex = r'^[\w.@+ -]+$'
    message = _('Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters, and spaces.')
    code = 'invalid_username'

    if not re.match(regex, value):
        raise ValidationError(
            message,
            code=code,
        )