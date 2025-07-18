from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from firebrigade.models import Entity, Membership
from django.contrib.auth.models import User

@login_required
def entities_JSON(request):
    """
    Devuelve un listado de todas las entidades disponibles.

    Solo accesible para usuarios autenticados.
    
    Respuesta:
        {
            "success": True,
            "entities": [
                {
                    "id": 1,
                    "name": "Primera Compañía"
                },
                {
                    "id": 2,
                    "name": "Comandancia"
                },
                ...
            ]
        }
    """
    entities = Entity.objects.all().values("id", "name")

    return JsonResponse({
        "success": True,
        "entities": list(entities)
    })




@login_required
def users_JSON(request):
    """
    Devuelve un listado de usuarios asociados a una entidad.

    Requiere el parámetro GET: entity_id

    Respuesta:
        {
            "success": True,
            "users": [
                {
                    "id": 1,
                    "username": "sebastian"
                },
                {
                    "id": 2,
                    "username": "jose"
                },
                ...
            ]
        }
    """
    entity_id = request.GET.get("entity_id")

    if not entity_id:
        return JsonResponse({
            "success": False,
            "error": "Falta parámetro 'entity_id'"
        }, status=400)

    # Obtener usuarios que pertenecen a esa entidad
    user_ids = Membership.objects.filter(entity_id=entity_id).values_list("user_id", flat=True)
    users = User.objects.filter(id__in=user_ids).values("id", "username")

    return JsonResponse({
        "success": True,
        "users": list(users)
    })