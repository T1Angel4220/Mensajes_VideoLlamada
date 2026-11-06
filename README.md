# Práctica: sistema de mensajes + SonarQube

Chat de texto (enviar y recibir), similar a WhatsApp, analizado con SonarQube.

## 1. Ejecutar el chat

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Abre http://127.0.0.1:5000

1. Crea dos cuentas (por ejemplo `ana` y `luis`, contraseña de 8+ caracteres).
2. En una ventana inicia sesión con una cuenta y en otra con la segunda (o usa dos navegadores).
3. Selecciona el contacto y envía mensajes de texto.

## 2. Instalar y levantar SonarQube

El comando `docker run -d --name sonarqube -p 9000:9000 sonarqube:latest` suele fallar en Windows porque Elasticsearch exige más memoria. Usa este:

```powershell
docker run -d --name sonarqube -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:lts-community
```

O con Compose:

```powershell
docker compose -f docker-compose.sonar.yml up -d
```

Espera 1-2 minutos y abre http://localhost:9000

- Usuario: `admin`
- Contraseña: `admin`
- Te pedirá cambiar la contraseña.

Cuando el servidor responde `UP`:

```powershell
curl http://localhost:9000/api/system/status
```

## 3. Analizar el código y ver la nota (A, B, C...)

```powershell
python -m pytest --cov=app --cov-report=xml --cov-report=term
```

Luego, con un token creado en SonarQube (My Account > Security > Generate Tokens):

```powershell
docker run --rm -e SONAR_HOST_URL=http://host.docker.internal:9000 -e SONAR_TOKEN=TU_TOKEN -v ${PWD}:/usr/src sonarsource/sonar-scanner-cli
```

En el proyecto **practica-envio-mensajes** verás:

- Reliability (fiabilidad)
- Security (seguridad)
- Maintainability (mantenibilidad)
- Coverage (cobertura de pruebas)

Esas son las letras A–E de SonarQube.
