# main/context_processors.py
def site_info(request):
    return {
        'current_user': request.user,
        'site_name': 'Bomberos Quintero',
        # aquí más datos globales si los necesitas
    }