Ing-Software
Proyecto Horizonte (nombre provisional)
Plataforma de seguimiento de trayectorias y riesgo de deserción escolar.

Descripción
El Proyecto Horizonte es una herramienta tecnológica diseñada para combatir la deserción escolar en liceos técnico-profesionales de zonas vulnerables. El sistema unifica los datos académicos, de asistencia y conductuales de los estudiantes con el fin de medir, comparar y alertar de manera oportuna a las autoridades pertinentes (profesores jefes, directivos, inspectores, duplas psicosociales y equipo de convivencia) sobre posibles riesgos de deserción escolar, y permite registrar y seguir las acciones de acompañamiento que se realizan con cada estudiante.

La plataforma es un apoyo a la gestión educativa: no reemplaza los sistemas oficiales del establecimiento ni toma decisiones automáticas sobre los estudiantes.

Integrantes
Mary González ----> Product Owner (PO)
Benjamín Farías ----> Scrum Master (SM)
Omar Millar ----> Developer (DEV)
Arquitectura
La arquitectura seleccionada corresponde a un Monolito Modular con Arquitectura Limpia (Clean Architecture) basada en principios de Arquitectura Hexagonal.

En la plataforma esto se refleja así:

Presentación: frontend React. Solo se comunica con el backend a través de frontend/src/api/cliente.js.
Entrada HTTP: backend/routers/, un archivo por módulo del Hito 1.
Reglas de negocio: backend/services/ (motor de riesgo, importación, seguimiento de casos, alertas, reportes).
Persistencia: backend/database.py es el único acceso a los datos (archivos CSV con escritura atómica).
Módulo del Hito 1	Dónde está
Usuarios y acceso	permisos.py, routers/auth.py, routers/usuarios.py, services/auth_service.py
Estudiantes	routers/estudiantes.py, services/estudiante_service.py, paginas/ficha/
Información académica	services/academico_service.py, services/importacion_service.py
Identificación de riesgos	services/riesgo_service.py, routers/riesgo.py, componentes/Semaforo.jsx
Seguimiento de casos	services/seguimiento_service.py, routers/seguimiento.py, paginas/MisCasos.jsx
Visualización y reportes	services/reporte_service.py, routers/reportes.py, paginas/Dashboard.jsx
Alertas y comunicaciones	services/notificacion_service.py, routers/notificaciones.py
Tecnologías y Herramientas
Lenguajes y Formatos: Python, JavaScript (JSX), JSON, CSV, SQL (esquema de la base de datos).
Backend: FastAPI + Uvicorn, Pydantic.
Frontend: React 19, Vite y Bootstrap 5.3.
Generador de fichas: Pandas, OpenPyXL.
Pruebas: pytest (backend), Vitest + React Testing Library (frontend) y pruebas de aceptación de la API.
Infraestructura y Servicios: Microsoft Services.
Herramientas de Gestión y Versionado: Jira, Git, GitHub.
Entorno de Desarrollo: Visual Studio Code.
Apoyo Inteligente: IA (Claude, Gemini).
Estructura del Repositorio

/proyecto

├── README.md
├── generador_fichas/            
│   ├── main.py   
│   ├── BD.xlsx
│   ├── RegistrosAuditoria.json
│   ├── src/
│   │   ├── generador_fichas.py
│   │   └── ficha_template.json
│   └── tests/

├── backend/                     
│   ├── main.py                  
│   ├── config.py                
│   ├── database.py              
│   ├── permisos.py              
│   ├── routers/                 
│   ├── schemas/                 
│   ├── services/                
│   ├── data/                    
│   ├── tests/                   
│   ├── pruebas/prueba_api.py    
│   ├── requirements.txt
│   └── requirements-dev.txt
└── frontend/                    
    ├── package.json
    └── src/
        ├── api/cliente.js       
        ├── componentes/         
        ├── hooks/               
        ├── paginas/             
        └── pruebas/             
Requisitos Previos e Instalación
Python 3.11 o superior (3.8 o superior basta para el generador de fichas).
Node.js 20 o superior.
Backend

cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app --reload
La API queda en http://127.0.0.1:8000 y su documentación interactiva en http://127.0.0.1:8000/docs.

Frontend (en otra terminal)

cd frontend
npm install
npm run dev
Abrir http://localhost:5173. Si el backend usa otra URL, copiar .env.example a .env y ajustar VITE_API_URL.

Primera carga de datos: la plataforma parte con la base vacía. Ingresar como administrador (contraseña demo1234), ir a Importar datos, seleccionar los 16 CSV de la base del liceo y presionar Cargar.

Generador de fichas (CLI)

cd generador_fichas
pip install pandas openpyxl
python main.py
Características Principales y Uso
Plataforma web
Inicio de sesión y permisos por rol: cada rol (administrador, director, jefe de UTP, profesor jefe, profesor, inspector, dupla psicosocial, equipo de convivencia) ve solo lo que le corresponde. El profesor jefe ve solo a su curso y los roles sin autorización no ven el nivel de riesgo (Ley 19.628).
Importación de datos (HU 1.1): carga de los CSV con validación de columnas, formatos, claves foráneas y reglas del modelo de datos. Si hay un solo error no se guarda nada y se informa el archivo y la línea.
Dashboard institucional (HU 1.2): tasas de asistencia, inasistencia y atrasos, asistencia por nivel, distribución de riesgo y tendencia mensual.
Lista de estudiantes con filtros (HU 1.4): búsqueda por nombre o RUT, nivel, especialidad TP y nivel de riesgo.
Semáforo de riesgo (HU 4.1, 4.3): Rojo, Amarillo o Verde por estudiante; al hacer clic se ven los factores que provocan la alerta.
Reglas de riesgo configurables (HU 4.2): umbral de asistencia, nota deficiente, cantidad de notas, ausencias consecutivas y operador lógico (Y/O). Solo el administrador puede cambiarlas.
Ficha integral del estudiante (HU 2.1 a 2.4): datos personales, apoderado (editable, teléfono de 9 dígitos), calendario de asistencia, calificaciones y anotaciones de convivencia.
Seguimiento de casos (HU 3.1 a 3.4): bitácora de intervenciones, línea de tiempo, derivación a la dupla psicosocial o al equipo de convivencia y contacto con el apoderado por WhatsApp.
Alertas y reportes (HU 4.4, 1.3): campana de notificaciones con alerta por 3 ausencias consecutivas y reporte semanal automático para los profesores jefes (viernes 14:00).
Generador de fichas (CLI)
Simulación de RBAC: al iniciar se pide el rol del usuario para enmascarar u ocultar datos sensibles.
Generador de Fichas de Estudiantes: conecta BD.xlsx con un modelo JSON y cruza la información del alumno con la de su apoderado y su especialidad.
Búsqueda y Filtrado: por nombre (coincidencia parcial), RUT exacto o ID de especialidad.
Edición y Auditoría: formulario con validación que modifica la base Excel y deja registro en RegistrosAuditoria.json.
Pruebas
# Pruebas unitarias del backend (pytest)
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -v

# Pruebas unitarias del frontend (Vitest)
cd frontend
npm install
npm test
Pruebas de aceptación de la API. Se ejecutan con el servidor levantado sobre una carpeta vacía, porque escriben datos:

cd backend
DATA_DIR=/tmp/datos_prueba uvicorn main:app --port 8001
python pruebas/prueba_api.py http://127.0.0.1:8001 ruta/a/los/CSV    # en otra terminal
Resultados (25-10-2026):

Tipo	Herramienta	Resultado
Unitarias backend	pytest	73/73 PASS
Unitarias frontend	Vitest + React Testing Library	21/21 PASS
Aceptación de la API (escenarios de las 16 HU)	pruebas/prueba_api.py	55/55 PASS
Las pruebas unitarias detectaron el defecto DEF-01: el teléfono del apoderado aceptaba dígitos no ASCII. Se corrigió en la versión v0.4.0.

Versiones y Flujo de Trabajo
Se trabaja con ramas feature/... que se integran a develop; develop se integra a main al cerrar cada entrega. Los mensajes de commit indican la HU (por ejemplo feat(HU-3.1): ...) y las tareas se gestionan en Jira.

Versión	Sprint	Contenido
v0.1.0	Sprint 1	Prototipo: carga de CSV, umbrales de riesgo (HU 4.2), lista con nivel de riesgo (HU 4.1) y dashboard (HU 1.2)
v0.2.0	Sprint 2	Diseño en capas del Hito 1, login y roles, importación validada, semáforo con motivos, filtros
v0.3.0	Sprint 2	Ficha integral del estudiante (HU 2.1 a 2.4)
v0.4.0	Sprint 2	Pruebas unitarias pytest y Vitest; corrección DEF-01
v0.5.0	Sprint 3	Seguimiento de casos: bitácora, WhatsApp, línea de tiempo y derivación (HU 3.1 a 3.4)
v0.6.0	Sprint 3	Alertas críticas (HU 4.4), reporte semanal (HU 1.3) y gestión de usuarios
v1.0.0	Sprint 3 / Hito 2	Pruebas de aceptación de la API y documentación final
Pendientes y Limitaciones
Importar archivos Excel (.xlsx) en la plataforma: por ahora solo se importan CSV.
Envío del reporte semanal por correo: requiere configurar un servidor SMTP (SMTP_HOST, SMTP_PORT, SMTP_USUARIO, SMTP_CONTRASENA, SMTP_REMITENTE).
HTTPS: depende del despliegue (Unidad III).
Las cuentas de demostración y la SECRET_KEY por defecto deben reemplazarse antes de usar datos reales.
Documentación del Proyecto
ERS: https://maryeugeniaxx01.atlassian.net/wiki/spaces/SCRUM/pages/7700481
Historias de usuario: https://maryeugeniaxx01.atlassian.net/wiki/spaces/SCRUM/pages/1736706
Tablero Jira: https://maryeugeniaxx01.atlassian.net/jira
