# Guía de Configuración: Google Drive API + AppSheet

Esta guía detalla los pasos necesarios para replicar este microservicio de generación de archivos Word desde AppSheet.

## 1. Configuración de Google Cloud (Drive API)

Para que el API pueda subir archivos a tu nombre, necesita permisos de OAuth2.

### A. Crear Proyecto y Habilitar API
1. Ve a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un nuevo proyecto.
3. En el buscador superior, escribe **"Google Drive API"** y haz clic en **Enable**.

### B. Configurar Pantalla de Consentimiento (OAuth Consent Screen)
1. Ve a **APIs & Services > OAuth consent screen**.
2. Elige **External** (si no tienes Google Workspace) o **Internal**.
3. Completa los datos obligatorios (App name, email).
4. En **Scopes**, agrega: `https://www.googleapis.com/auth/drive`.
5. **IMPORTANTE:** Agrega tu correo como "Test User" si el proyecto está en estado "Testing".

### C. Crear Credenciales (OAuth Client ID)
1. Ve a **APIs & Services > Credentials**.
2. Haz clic en **Create Credentials > OAuth client ID**.
3. **Application type**: Web application.
4. **Authorized redirect URIs**: Agrega `https://developers.google.com/oauthplayground`. (Esto es vital para obtener el Refresh Token).
5. Copia tu **Client ID** y **Client Secret**.

### D. Obtener el Refresh Token
1. Ve a [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/).
2. Haz clic en el icono de engranaje (Settings) arriba a la derecha.
3. Activa **"Use your own OAuth credentials"** e ingresa tu Client ID y Client Secret.
4. En la lista de la izquierda, busca **Drive API v3** y selecciona el scope `.../auth/drive`.
5. Haz clic en **Authorize APIs** e inicia sesión con tu cuenta de Google.
6. En el Step 2, haz clic en **Exchange authorization code for tokens**.
7. Copia el **Refresh Token** (no el Access Token, ya que este último expira pronto).

---

## 2. Configuración de AppSheet

### A. Habilitar la API
1. En el editor de AppSheet, ve a **Manage > Integrations > IN: cloud services**.
2. Activa **Enable**.
3. Genera una **Access Key** y cópiala.
4. Anota tu **App ID** (está en la misma pantalla).

### B. Crear el Webhook (Bot)
1. Ve a **Automation > Bots** y crea uno nuevo.
2. **Event**: Por ejemplo, al crear una fila o al cambiar un estado.
3. **Process**: Elige **Call a webhook**.
4. **Url**: La URL de tu servicio en Render (ej. `https://tu-app.onrender.com/api/v1/menus/generate?upload_to_drive=true`).
5. **HTTP Verb**: POST.
6. **HTTP Content Type**: JSON.
7. **Body**: Usa esta estructura:
   ```json
   {
     "event_id": "<<[ID]>>",
     "event_name": "<<[Event_Name]>>",
     "all_meals": [ ... tus datos ... ]
   }
   ```

### C. Botón de Descarga
1. Crea una **Action** de tipo `External: open a file`.
2. En la fórmula de la URL, usa la columna donde el API guarda el link.
3. Esto descargará el archivo directamente gracias al `webContentLink`.

---

## 3. Variables de Entorno (Render)

En el panel de Render, agrega estas variables:

| Variable | Descripción |
| :--- | :--- |
| `GOOGLE_CLIENT_ID` | De Google Cloud Credentials |
| `GOOGLE_CLIENT_SECRET` | De Google Cloud Credentials |
| `GOOGLE_REFRESH_TOKEN` | Obtenido en OAuth Playground |
| `GOOGLE_DRIVE_FOLDER_ID` | El ID de la carpeta de Drive (está en la URL de la carpeta) |
| `APPSHEET_APP_ID` | De Manage > Integrations |
| `APPSHEET_ACCESS_KEY` | De Manage > Integrations |

---

## 4. Notas Técnicas Relevantes
- **Plantilla Word:** El archivo `general_sign.docx` debe estar en la raíz del proyecto.
- **Formato:** El código utiliza `sectPr.vAlign_val = 'center'` para el centrado vertical, que es compatible nativamente con Microsoft Word.
