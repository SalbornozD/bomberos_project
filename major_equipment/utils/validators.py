import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_chilean_plate(plate: str) -> None:
    """
    Valida que la placa chilena tenga el formato correcto.
    Formato antiguo: 2 letras + 4 digitos (Ej AB1234)
    Formato nuevo: 4 letras + 2 digitos (Ej ABCD12)
    """

    # Expresión regular para validar los formatos de placa
    pattern = re.compile(r'^(?:[A-Z]{2}\d{4}|[A-Z]{4}\d{2})$')

    # En caso de que la placa no cumpla con el formato, lanzar una excepción
    if not pattern.match(plate):
        raise ValidationError(
            _("La placa debe tener el formato AB1234 o ABCD12."),
            params={'plate': plate},
        )
    return plate

