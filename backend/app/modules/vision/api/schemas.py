from pydantic import BaseModel, Field


class TagOut(BaseModel):
    name: str = Field(description="Etiqueta en minúsculas, normalmente en inglés (p. ej. 'food').")
    confidence: float = Field(description="Confianza entre 0 y 1.")


class ImageAnalysisOut(BaseModel):
    ocr_lines: list[str] = Field(description="Líneas de texto leídas, en orden.")
    tags: list[TagOut]
    caption: str | None = Field(description="Descripción corta de la imagen, si la hay.")


class ErrorOut(BaseModel):
    code: str
    message: str
