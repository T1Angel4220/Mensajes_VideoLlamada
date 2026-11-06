import {

  Callout,

  Card,

  CardBody,

  CardHeader,

  Divider,

  Grid,

  H1,

  H2,

  H3,

  Pill,

  Row,

  Stack,

  Stat,

  Table,

  Text,

  useHostTheme,

} from "cursor/canvas";

const FINDINGS = [

  [

    "C-01",

    "Alta",

    "database.py",

    "Confirmado",

    "except Exception genérico en get_connection: oculta la clase de fallo y obliga a rollback indiscriminado.",

  ],

  [

    "C-02",

    "Alta",

    "database.py",

    "Confirmado",

    "SQLite no activa PRAGMA foreign_keys=ON. Las FOREIGN KEY del esquema no se aplican en el runtime por defecto.",

  ],

  [

    "C-03",

    "Alta",

    "models.py / routes",

    "Confirmado",

    "Sin control de fuerza bruta ni bloqueo de cuenta. authenticate acepta intentos ilimitados.",

  ],

  [

    "C-04",

    "Media",

    "models.py",

    "Confirmado",

    "Política de contraseña insuficiente: solo longitud 8 y ausencia de espacios. No exige complejidad.",

  ],

  [

    "C-05",

    "Media",

    "app/__init__.py",

    "Confirmado",

    "Clave de firma persistida en claro en .secret_key. SESSION_COOKIE_SECURE no está definido. WTF_CSRF_SSL_STRICT=False.",

  ],

  [

    "C-06",

    "Media",

    "models.py / chat",

    "Confirmado",

    "list_users expone todos los usuarios a cualquier sesión autenticada. No hay modelo de contactos ni consentimiento.",

  ],

  [

    "C-07",

    "Media",

    "models.py + routes.py",

    "Confirmado",

    "SRP roto: validación, persistencia SQL y reglas de negocio conviven en models.py; HTTP, sesión y ensamblado JSON en routes.py.",

  ],

  [

    "C-08",

    "Media",

    "tests/",

    "Confirmado",

    "4 pruebas. Cubren camino feliz y validaciones básicas. No hay prueba de CSRF rechazado, XSS, IDOR entre terceros, ni fuerza bruta.",

  ],

  [

    "C-09",

    "Baja",

    "routes.py",

    "Confirmado",

    "Duplicación de conocimiento: extracción username/password y plantilla AUTH repetidas en login y registro.",

  ],

  [

    "C-10",

    "Baja",

    "chat.js",

    "Confirmado",

    "Polling cada 2500 ms sin backoff; errores de red y HTTP no 2xx se silencian.",

  ],

];

export default function AuditoriaCalidadSoftware() {

  const theme = useHostTheme();

  return (

    <Stack gap={20} style={{ padding: 20 }}>

      <Stack gap={6}>

        <H1>Dictamen de auditoría — Sistema de envío de mensajes</H1>

        <Text tone="secondary">

          Auditoría estática independiente sobre el código fuente presente en

          Practica_EnvioMensajes. Criterio: Clean Code, SOLID, OWASP y evidencia

          comprobable. Fecha de revisión: 4 de noviembre de 2026. Alcance: app/,

          tests/, run.py, plantillas y chat.js.

        </Text>

      </Stack>

      <Grid columns={4} gap={12}>

        <Stat value="C" label="Calificación global" tone="warning" />

        <Stat value="C+" label="Seguridad demostrada" tone="warning" />

        <Stat value="C" label="Diseño / SOLID" tone="warning" />

        <Stat value="C" label="Pruebas" tone="warning" />

      </Grid>

      <Callout tone="warning" title="La A de SonarQube no equivale a A de auditoría">

        SonarQube mide reglas, bugs, duplicación detectada y cobertura de

        líneas. Esta auditoría mide diseño, amenazas y profundidad de evidencia.

        Un Quality Gate Passed con letras A no demuestra arquitectura

        mantenible ni controles OWASP completos. No se reconfirmó SonarQube en

        este acto (API 401). Las medidas A/0 bugs/93–94% cobertura quedan como

        evidencia de sesión previa, no como nota de este dictamen.

      </Callout>

      <H2>Veredicto</H2>

      <Text>

        El programa es un chat 1-a-1 de texto con registro, sesión, hash de

        contraseña, consultas parametrizadas, CSRF y escape XSS en el cliente

        (textContent). Eso es código funcional con controles básicos reales. No

        es código de calidad empresarial: hay mezcla de responsabilidades,

        política de autenticación débil, claves en disco, FKs no exigidas,

        ausencia de logging y una batería de pruebas superficial. Calificación

        C: aceptable como práctica universitaria, insuficiente para B o A.

      </Text>

      <H2>Métricas obtenidas del código</H2>

      <Text size="small" tone="tertiary">

        Fuente: conteo de líneas no vacías/no comentario y complejidad

        ciclomática aproximada por AST (If/For/While/Except/BoolOp/Assert/comprensiones).

        No es el motor de SonarQube.

      </Text>

      <Grid columns={4} gap={12}>

        <Stat value="328" label="LOC código de producción (app+run)" />

        <Stat value="131" label="LOC tests" />

        <Stat value="6" label="Máx. complejidad (api_enviar)" />

        <Stat value="4" label="Casos de prueba" />

      </Grid>

      <Table

        headers={["Unidad", "LOC código", "Complejidad máx.", "Observación"]}

        rows={[

          ["app/__init__.py", "40", "3", "Fábrica Flask + secreto"],

          ["app/database.py", "41", "2", "except Exception"],

          ["app/models.py", "102", "4", "Validación + SQL juntos"],

          ["app/routes.py", "141", "6", "HTTP + orquestación"],

          ["run.py", "4", "1", "Bind 127.0.0.1, debug=False"],

          ["tests/*", "131", "—", "4 tests, camino principal"],

        ]}

        columnAlign={["left", "right", "right", "left"]}

        striped

      />

      <H2>Hallazgos</H2>

      <Table

        headers={["ID", "Severidad", "Ubicación", "Estado", "Hallazgo"]}

        rows={FINDINGS}

        rowTone={[

          "danger",

          "danger",

          "danger",

          "warning",

          "warning",

          "warning",

          "warning",

          "warning",

          "info",

          "info",

        ]}

        striped

        stickyHeader

      />

      <H2>Controles de seguridad verificados en código</H2>

      <Grid columns={2} gap={12}>

        <Card>

          <CardHeader trailing={<Pill tone="success" size="sm">Presente</Pill>}>

            Controles confirmados

          </CardHeader>

          <CardBody>

            <Stack gap={6}>

              <Text>

                SQL parametrizado en todos los execute observados. Hash

                pbkdf2:sha256 con salt 16. session.clear() antes de autenticar.

                Cookie HttpOnly y SameSite=Lax. CSRFProtect + token en formularios

                y X-CSRFToken en POST JSON. conversation filtra por el user_id de

                sesión (no lee chats ajenos entre terceros). chat.js usa

                textContent. Jinja2 autoescape por defecto. MAX_CONTENT_LENGTH 16

                KiB. debug=False. bind 127.0.0.1.

              </Text>

            </Stack>

          </CardBody>

        </Card>

        <Card>

          <CardHeader trailing={<Pill tone="warning" size="sm">Ausente</Pill>}>

            Controles no implementados

          </CardHeader>

          <CardBody>

            <Text>

              Rate limiting / lockout. Complejidad de contraseña. Cookie Secure.

              CSRF SSL strict. PRAGMA foreign_keys. Logging de autenticación

              fallida. HTTPS. Autorización de contactos. Paginación de mensajes.

              Cabeceras de seguridad HTTP (CSP, HSTS). Rotación de clave de

              sesión. Pruebas de seguridad negativas.

            </Text>

          </CardBody>

        </Card>

      </Grid>

      <H2>OWASP — mapeo a evidencia</H2>

      <Table

        headers={["Categoría", "Dictamen", "Evidencia en código"]}

        rows={[

          [

            "A03 Injection",

            "Mitigado en SQL",

            "Placeholders ? en INSERT/SELECT. XSS de salida en DOM: textContent. Plantillas: autoescape (no se desactiva).",

          ],

          [

            "A07 Identification/Auth",

            "Parcial",

            "Hash correcto. Política débil. Sin lockout. Login no valida formato de usuario más allá de strip.",

          ],

          [

            "A01 Broken Access Control",

            "Parcial",

            "login_required y filtro de conversación por sesión: OK. Directorio global de usuarios: fuga de existencia.",

          ],

          [

            "A02 Cryptographic failures",

            "Parcial",

            "pbkdf2 presente. Clave de firma en archivo plano. Sin Secure cookie.",

          ],

          [

            "A04 Insecure design",

            "Riesgo",

            "Cualquier usuario ve a todos. No hay modelo de amistad ni consentimiento.",

          ],

          [

            "A05 Security misconfiguration",

            "Riesgo",

            "WTF_CSRF_SSL_STRICT=False. FK SQLite no aplicadas. Sin cabeceras de seguridad.",

          ],

          [

            "A08 Software integrity",

            "No verificado",

            "requirements.txt fija versiones. No hay lockfile de hashes ni verificación de imagen Docker en esta revisión.",

          ],

          [

            "A09 Logging/monitoring",

            "Deficiente",

            "No hay logging de seguridad ni de errores de autenticación.",

          ],

        ]}

        striped

      />

      <H2>SOLID</H2>

      <Table

        headers={["Principio", "Nota", "Hecho observable"]}

        rows={[

          [

            "SRP",

            "No cumplido",

            "models.py valida, hashea y ejecuta SQL. routes.py autentica, renderiza y arma API.",

          ],

          [

            "OCP",

            "No demostrado",

            "Añadir grupos, adjuntos o cifrado implica reescribir conversation y las rutas, no extender.",

          ],

          [

            "LSP",

            "No aplica",

            "No hay jerarquía de tipos más allá de ValidationError(ValueError).",

          ],

          [

            "ISP",

            "No aplica",

            "No hay interfaces. La ausencia de interfaces no acredita ISP.",

          ],

          [

            "DIP",

            "No cumplido",

            "La capa de aplicación depende de sqlite3.Connection concreto. No hay puerto de repositorio.",

          ],

        ]}

        rowTone={["danger", "warning", "info", "info", "danger"]}

      />

      <H2>Revisión por archivo</H2>

      <Stack gap={10}>

        <Card>

          <CardHeader>app/models.py — núcleo de negocio</CardHeader>

          <CardBody>

            <Text>

              Nombres claros y validaciones explícitas. Consultas

              parametrizadas. El módulo no es un modelo de dominio: es un

              repositorio procedural. authenticate no reutiliza

              validate_username, así que el ingreso admite cadenas que el

              registro rechazaría (p. ej. espacios internos se rechazan al

              crear, pero login solo hace strip). IntegrityError se traduce

              bien a ValidationError.

            </Text>

          </CardBody>

        </Card>

        <Card>

          <CardHeader>app/routes.py — adaptador HTTP</CardHeader>

          <CardBody>

            <Text>

              Separación GET/POST por endpoint es correcta. login_required

              distingue API y HTML. api_enviar complejidad 6, aún bajo umbral

              típico 15, pero concentra validación HTTP + persistencia. No hay

              manejo de errores no-ValidationError (JSON malformado silencioso

              vía silent=True).

            </Text>

          </CardBody>

        </Card>

        <Card>

          <CardHeader>app/database.py y __init__.py</CardHeader>

          <CardBody>

            <Text>

              Contexto de conexión y commit/rollback existen. except Exception

              es inaceptable en auditoría. init_db en cada create_app es

              aceptable en lab, no en producción. La clave se genera con

              secrets.token_hex(32) — adecuado — y luego se guarda en claro.

            </Text>

          </CardBody>

        </Card>

        <Card>

          <CardHeader>Frontend</CardHeader>

          <CardBody>

            <Text>

              XSS de inserción de mensajes mitigado con textContent. encodeURIComponent

              en query. CSRF enviado en POST. No hay prueba automatizada de

              esto. Fallos de envío no se muestran al usuario. El intervalo fijo

              es diseño frágil, no vulnerabilidad por sí sola.

            </Text>

          </CardBody>

        </Card>

      </Stack>

      <H2>Pruebas — qué cubren y qué no</H2>

      <Grid columns={2} gap={12}>

        <Stack gap={8}>

          <H3>Cubierto (confirmado en tests/)</H3>

          <Text>

            Usuario corto, contraseña corta, espacios, mensaje vacío y de 1001

            caracteres. Duplicado de username. Autenticación fallida. Auto-mensaje.

            Destinatario inexistente. API sin sesión 401. Flujo de envío entre

            dos usuarios con CSRF válido.

          </Text>

        </Stack>

        <Stack gap={8}>

          <H3>No cubierto</H3>

          <Text>

            POST sin CSRF (debe ser 400). Inyección SQL. Payload XSS persistente.

            Lectura de conversación ajena. Contraseña exactamente 8 vs 7 ya está;

            complejidad extra no. Concurrent writes SQLite. lastrowid nulo.

            Cabecera CSRF incorrecta. Registro con caracteres unicode fuera de

            USERNAME_CHARS sí está vía validate_username, no vía HTTP dedicado.

          </Text>

        </Stack>

      </Grid>

      <Callout tone="info" title="Cobertura de líneas no es cobertura de riesgo">

        Una cobertura de líneas ~94% (pytest --cov, sesión previa) no implica

        que los controles de seguridad estén probados. Las líneas de CSRF y

        hash se ejecutan en el camino feliz; no hay aserción de que el control

        falle cerrado.

      </Callout>

      <H2>Qué no se verificó</H2>

      <Text>

        No se ejecutó pentest, fuzzing ni prueba de carga. No se inspeccionó

        mensajes.db en busca de hashes reales de usuarios de demo. No se

        reconfirmó el Quality Gate de SonarQube en este acto (HTTP 401). No se

        auditó el contenedor Docker ni la configuración de red del host. No se

        afirma existencia de vulnerabilidades de ejecución remota: el servidor

        de desarrollo escucha solo en 127.0.0.1, lo cual reduce exposición, no

        la calidad del diseño.

      </Text>

      <Divider />

      <Row gap={8} align="center">

        <Pill tone="warning">Dictamen C</Pill>

        <Text tone="secondary" size="small">

          No se otorga B: faltan profundidad de pruebas, separación de capas y

          controles de autenticación/operación. No se otorga D: hay hash,

          SQL seguro, CSRF, alcance de conversación y escape XSS demostrables.

        </Text>

      </Row>

      <Text size="small" tone="tertiary">

        Criterio uniforme de auditoría académica/empresarial. Paleta: tokens del

        host. Alcance limitado al árbol de código citado.

      </Text>

    </Stack>

  );

}