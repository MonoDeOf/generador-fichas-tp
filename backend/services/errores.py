class ErrorNegocio(Exception):
    """Error controlado que se traduce a una respuesta HTTP con un mensaje en JSON."""

    def __init__(self, codigo: int, mensaje: str, detalles: list | None = None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles or []
