# Espacio para el pipeline de integración y despliegue

Este documento queda reservado para la creación y revisión del pipeline CI/CD de BackFinanzas.

## Estado actual

El repositorio tiene un workflow de integración para el backend en
`.github/workflows/backend.yml`. Actualmente valida:

- Ruff;
- formato Ruff;
- mypy;
- pytest con cobertura mínima;
- contrato OpenAPI.

Todavía no se ha definido un pipeline de despliegue automático.

## Información que debe completarse

- Plataforma de ejecución:
- Ambientes:
- Estrategia de ramas:
- Registro de imágenes:
- Variables y secretos:
- Ejecución de migraciones:
- Health checks:
- Rollback:
- Observabilidad:
- Aprobaciones:
- Responsable de revisión:
- Fecha de revisión:

## Criterios mínimos de revisión

- El pipeline no imprime secretos.
- Las pruebas se ejecutan antes de desplegar.
- Las migraciones son versionadas y reversibles cuando sea posible.
- Producción requiere aprobación explícita.
- El despliegue verifica `/health`.
- Existe una estrategia documentada de rollback.
- Los permisos de GitHub Actions son mínimos.
- El pipeline distingue fallos de aplicación, infraestructura y configuración.

