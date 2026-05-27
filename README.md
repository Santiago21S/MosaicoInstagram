# 🧩 MosaicoInstagram

MosaicoInstagram es una aplicación web basada en Django que permite mezclar imágenes, aplicar filtros y generar un mosaico de 9 piezas (3x3) optimizado para el grid de Instagram. Todo el procesamiento de imágenes se realiza en segundo plano utilizando Celery y Redis.

## 🚀 Requisitos Previos

- Python 3.10+
- MariaDB Server (para la base de datos)
- Redis Server (broker para Celery)

## 🛠️ Instalación y Configuración

1. **Clonar el repositorio y crear entorno virtual:**
   ```bash
   git clone https://github.com/Santiago21S/MosaicoInstagram.git
   cd MosaicoInstagram
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno:**
   Copia el archivo de ejemplo y configúralo con tus credenciales de MariaDB y Redis.
   ```bash
   cp .env.example .env
   ```
   Abre `.env` y asegúrate de que los datos de `DB_NAME`, `DB_USER`, y `DB_PASSWORD` coincidan con tu servidor MariaDB local.

4. **Crear base de datos y correr migraciones:**
   Entra a tu servidor de MariaDB y crea la base de datos:
   ```sql
   CREATE DATABASE mosaico_db;
   ```
   Luego ejecuta las migraciones de Django:
   ```bash
   python manage.py migrate
   ```

5. **Crear un superusuario:**
   ```bash
   python manage.py createsuperuser
   ```

## ⚙️ Ejecución del Proyecto

Para correr la aplicación de forma completa, necesitas iniciar tanto el servidor web de Django como el worker de Celery en terminales separadas.

**Terminal 1: Servidor Django**
```bash
source venv/bin/activate
python manage.py runserver
```

**Terminal 2: Worker de Celery**
Asegúrate de que Redis esté corriendo (por ejemplo, con `redis-server`), luego inicia el worker:
```bash
source venv/bin/activate
celery -A config worker --loglevel=info
```

Ahora puedes visitar `http://127.0.0.1:8000/` y empezar a crear mosaicos.

## 🧪 Pruebas (Tests)

El proyecto incluye pruebas automatizadas (APIs, vistas HTML, y flujo de integración). Para ejecutarlas con reporte de cobertura:

```bash
pytest mosaico/tests/ --cov=mosaico --cov-report=term-missing
```

> **Nota:** Las pruebas configuran Celery para ejecutarse sincrónicamente (`CELERY_TASK_ALWAYS_EAGER=True`), por lo que no requieren que el worker de Celery ni Redis estén corriendo.

## 📝 Créditos

**Nombres y Matrículas:**
- Santiago Sanabria Basurto A01773072
- Mauricio Gonzalez Segovia A01770038
- Hannah Becerrill Guadarrama A0176951
