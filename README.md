# 🤖 Proyecto Base: Chatbot con IA para WhatsApp Business (WABA)

## 📘 Descripción general

Este proyecto es una **base inicial** para crear chatbots con **inteligencia artificial (IA)** integrados a **WhatsApp Business (WABA)**.  
Su objetivo es ofrecer una estructura lista para conectar con la API de Meta y servir como punto de partida para futuros desarrollos más avanzados o personalizados.

El propósito principal es que otros desarrolladores puedan comprender cómo se construye la conexión entre WhatsApp y un modelo de IA, y cómo adaptar el bot a distintos escenarios: atención al cliente, ventas, portafolios de empresa o automatización de tareas.

> 🧠 **Importante:** este proyecto está en fase de desarrollo para pasar a pruebas.  
> No se recomienda su uso en producción sin las configuraciones de seguridad y privacidad adecuadas.

---

## 💡 Objetivo del proyecto

- Crear una **base sólida y reutilizable** para conectar WhatsApp con un motor de inteligencia artificial.  
- Facilitar la comprensión del **flujo entre Meta (WABA), el servidor y la IA**.  
- Ofrecer un ejemplo funcional que permita construir versiones más complejas con el mismo esquema.  
- Integrar el **portafolio de la empresa** dentro del chatbot, para que los usuarios puedan conocer productos o servicios directamente desde WhatsApp.

---

## 🧩 Cómo funciona (explicado en pasos simples)

1. **Recepción de mensajes:**  
   Cuando un usuario escribe al número de WhatsApp Business, Meta envía el mensaje al servidor de este proyecto mediante un **webhook**.

2. **Procesamiento con IA:**  
   El mensaje recibido se interpreta mediante una **IA integrada (por ejemplo, OpenAI o un modelo local)**, que analiza la intención del usuario y genera una respuesta adecuada.

3. **Envío de respuesta:**  
   El servidor responde al usuario en WhatsApp usando la API de Meta.  
   Esto puede incluir texto, imágenes, botones o enlaces según la lógica del bot.

4. **Registro y monitoreo:**  
   Los mensajes y métricas básicas (como errores, latencia o cantidad de mensajes) se guardan o monitorean para mejorar el rendimiento y la calidad de las respuestas.

---

## ⚙️ Estructura general del proyecto

| Carpeta / Archivo | Descripción |
|--------------------|-------------|
| `main.py` | Código principal del servidor que maneja los mensajes y las conexiones con Meta. |
| `firestore.py` / `firestore_prod.py` | Scripts para guardar información en Firestore (mensajes, usuarios, estadísticas). |
| `api.yaml` | Archivo que define los endpoints y estructura de la API. |
| `body.json`, `auth_url.txt` | Archivos de ejemplo para pruebas de conexión con Meta. |
| `Dockerfile` | Permite ejecutar el proyecto dentro de un contenedor para mayor facilidad de despliegue. |
| `requirements.txt` | Lista de dependencias necesarias para correr el proyecto. |
| `*.json` (métricas y alertas) | Configuraciones de monitoreo (por ejemplo, error rate, latencia, uptime). |
| `.secrets.baseline` | Archivo de control para evitar subir claves o contraseñas por error. |

---

## 🚀 Cómo usar este proyecto

> Estas instrucciones son de nivel básico para que cualquier programador pueda iniciar sin experiencia previa en Meta o IA.

### 1️⃣ Clona el repositorio
```bash
git clone https://github.com/Rocuts/whatsapp-api-test.git
cd whatsapp-api-test
2️⃣ Crea un entorno virtual e instala las dependencias
bash
Copiar código
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
3️⃣ Configura tus variables de entorno
Crea un archivo .env en la raíz del proyecto con las siguientes claves:

bash
Copiar código
META_TOKEN=<tu_token_de_meta>
PHONE_ID=<tu_id_de_numero_waba>
GOOGLE_APPLICATION_CREDENTIALS=<ruta_a_tu_key.json>
4️⃣ Ejecuta el servidor (modo desarrollo)
bash
Copiar código
uvicorn main:app --reload --host 0.0.0.0 --port 8000
5️⃣ Conecta el webhook en Meta Developer
Ve a developers.facebook.com

Crea una app de tipo “Business”.

Configura el webhook URL con la dirección de tu servidor.

Verifica el token de validación y comienza a recibir mensajes de prueba.

🔐 Seguridad y privacidad
No compartas el archivo key.json ni tus tokens de Meta.
Estos deben almacenarse como variables de entorno, nunca subirse al repositorio.

Si el proyecto se publica, asegúrate de rotar las credenciales anteriores.

No uses datos reales de clientes mientras el proyecto esté en desarrollo o pruebas.

Revisa periódicamente los archivos de configuración (.gitignore, .secrets.baseline) para evitar filtraciones.

🧭 Próximos pasos
 Completar el flujo de verificación del webhook de Meta.

 Añadir respuestas automáticas más naturales con IA.

 Incluir ejemplos de portafolio de productos o servicios.

 Mejorar la documentación técnica (instalación, despliegue, conexión con IA).

 Crear una versión productiva en la nube (ej. Cloud Run o AWS).

👥 Equipo y créditos
Desarrollado por Rocuts como proyecto base para futuros chatbots con IA integrados a WhatsApp Business.
Pensado para desarrolladores que desean aprender o implementar soluciones inteligentes de mensajería sin experiencia previa en IA o Meta.

🧾 Licencia
Este proyecto se distribuye bajo una licencia abierta para fines educativos y de desarrollo interno.
Revisa las condiciones antes de su uso comercial.