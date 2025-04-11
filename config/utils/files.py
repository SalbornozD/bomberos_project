import os

def delete_file(path: str) -> None:
    """
    Elimina un archivo del sistema de archivos si existe.

    Parámetros:
        path (str): Ruta absoluta del archivo.

    Retorno:
        None
    """
    if path and os.path.isfile(path):
        os.remove(path)