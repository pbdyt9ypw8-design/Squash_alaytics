# Docker: SquashAnalytics

## Arranque local

1. Copia `.env.example` a `.env` y define `POSTGRES_PASSWORD` con una contraseña segura y URL-safe. No publiques `.env`.
2. Desde la raíz del repositorio ejecuta:

   ```bash
   docker compose up --build -d
   ```

3. Comprueba los servicios y la API:

   ```bash
   docker compose ps
   curl http://localhost:8000/
   ```

Docker inicializa TimescaleDB con `db-init/001_schema.sql` y después ejecuta la migración existente `migrations/20261110_kinematics_and_point_events.sql`. Los scripts de `/docker-entrypoint-initdb.d` solo se ejecutan cuando el volumen de datos está vacío.

## Reinicializar la base de datos de desarrollo

Si ya arrancaste la base de datos antes de agregar estos scripts, o quieres volver a crearla desde cero, los scripts no se ejecutarán automáticamente mientras exista el volumen. **Este comando elimina permanentemente los datos del volumen local**:

```bash
docker compose down -v
docker compose up --build -d
```

Para conservar datos existentes, aplica el esquema/migración manualmente y crea una copia de seguridad antes de modificar la base.

## Esquema inicial

El esquema incluye las tablas consultadas por la API (`partidos`, `jugadores`, `telemetria_frames`, `metricas_metabolicas`) y la migración crea `eventos_puntos` y añade columnas cinemáticas opcionales. Se pueden insertar partidos y jugadores desde SQL antes de enviar telemetría; la API actual no ofrece endpoints para crear esos registros.
