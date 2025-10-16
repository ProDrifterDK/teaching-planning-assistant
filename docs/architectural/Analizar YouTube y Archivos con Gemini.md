

# **Guía para Desarrolladores sobre Análisis Multimodal con la API de Gemini: Desde URLs de YouTube hasta Archivos Locales**

## **Introducción: El Paradigma de la Multimodalidad Nativa**

### **Visión General**

La familia de modelos Gemini representa un avance fundamental en la inteligencia artificial, construida desde cero con la multimodalidad como principio de diseño central.1 A diferencia de los sistemas que añaden capacidades de visión o audio a un modelo de lenguaje preexistente, la arquitectura nativa de Gemini le permite razonar de manera fluida y sofisticada a través de texto, imágenes, video y audio dentro de una única plataforma unificada. Esta integración inherente desbloquea una amplia gama de tareas de procesamiento de imágenes y visión por computadora, como la subtitulación de imágenes, la clasificación y la respuesta a preguntas visuales, sin necesidad de entrenar modelos de aprendizaje automático especializados.2

### **Planteamiento del Problema**

Los desarrolladores se enfrentan habitualmente al desafío de procesar y extraer valor de grandes volúmenes de datos de medios no estructurados. Tareas que van desde la transcripción y resumen de videoconferencias hasta la extracción de datos específicos de imágenes o documentos pueden requerir complejas cadenas de herramientas y una experiencia considerable en procesamiento de medios.1 La API de Gemini se presenta como una solución potente y consolidada a estos desafíos, ofreciendo un único punto de acceso para realizar análisis complejos que combinan la comprensión visual, auditiva y textual.1

### **Hoja de Ruta del Informe**

Este informe sirve como una guía técnica exhaustiva para desarrolladores que deseen aprovechar las capacidades multimodales de la API de Gemini. La estructura está diseñada para construir el conocimiento de manera progresiva:

1. **Conceptos Fundamentales:** Se establecerán los conocimientos previos esenciales, cubriendo la autenticación y la estructura fundamental de una solicitud a la API.  
2. **Análisis de Videos de YouTube:** Se realizará una inmersión profunda en el caso de uso principal de analizar videos de YouTube directamente desde su URL.  
3. **Manejo de Archivos:** Se proporcionará una guía completa para enviar y procesar diversos tipos de archivos locales y remotos.  
4. **Guía de Referencia:** Se ofrecerá una sección de referencia detallada con especificaciones técnicas, formatos soportados y limitaciones operativas.

## **Sección 1: Conceptos Fundamentales: Autenticación y Estructura de la API**

Antes de realizar cualquier solicitud multimodal, es crucial comprender el ecosistema de la API de Gemini, cómo autenticarse y la anatomía de una solicitud. Esta base es indispensable para una implementación exitosa y escalable.

### **1.1. El Ecosistema de la API de Gemini: Google AI Studio vs. Vertex AI**

El acceso a los modelos Gemini se ofrece principalmente a través de dos vías, cada una diseñada para un perfil de desarrollador diferente. La documentación presenta dos flujos de configuración distintos: uno basado en una simple clave de API obtenida de un sitio web (Google AI Studio) y otro que implica una configuración completa de un proyecto en la nube (Vertex AI).6 Esta bifurcación no es accidental, sino que refleja una estrategia de producto deliberada para atender a diferentes casos de uso y escalas.

La elección del método de autenticación determina fundamentalmente el flujo de trabajo de desarrollo, los SDKs aplicables y el modelo de precios. Aclarar esta distinción desde el principio es el concepto fundacional más importante para evitar la frustración del desarrollador y asegurar que se consulte la documentación correcta.

#### **Autenticación mediante Clave de API de AI Studio**

Para un desarrollo y prototipado rápidos, Google AI Studio ofrece una vía de bajo rozamiento.6 Este enfoque es ideal para desarrolladores individuales, investigadores y aficionados. El proceso para obtener una clave es sencillo:

1. Navegar al sitio web de Google AI Studio.  
2. Iniciar sesión con una cuenta de Google.  
3. Hacer clic en el botón "Get API Key" y aceptar los términos del servicio.  
4. Google generará una clave de API única que debe ser copiada y almacenada de forma segura.6

Es de vital importancia tratar esta clave de API como una contraseña: no debe compartirse públicamente ni incluirse en código fuente visible para otros, ya que cualquiera con la clave puede utilizar la cuota de la API asociada.6

#### **Contextualización de Vertex AI**

En contraste, Vertex AI es la plataforma de nivel empresarial de Google Cloud para construir e implementar aplicaciones de IA.8 El acceso a Gemini a través de Vertex AI está diseñado para aplicaciones que requieren escalabilidad, seguridad robusta a través de roles IAM (Identity and Access Management) e integración con el ecosistema más amplio de Google Cloud. Este camino implica una configuración más elaborada, que incluye la creación de un proyecto de Google Cloud, la habilitación de la facturación y la asignación de roles de IAM específicos, como "Vertex AI User" (roles/aiplatform.user).7

### **1.2. Deconstruyendo una Solicitud Multimodal: Contenidos, Partes y Datos**

Independientemente del método de autenticación, la estructura de una solicitud al endpoint generateContent sigue un formato JSON consistente. Comprender esta "gramática" de la API es esencial para formular prompts multimodales efectivos.9

#### **La Estructura JSON Central**

Una solicitud típica se compone de un objeto JSON con una clave principal, contents.

* **Array contents:** Este es un array que representa los turnos en una conversación. Para una simple solicitud, contendrá un solo objeto. Para mantener un historial de chat, se pueden incluir múltiples objetos, cada uno representando un turno del usuario o del modelo.9  
* **Array parts:** Dentro de cada objeto content, se encuentra el array parts. Este es el corazón de una solicitud multimodal. Cada elemento de este array es un objeto Part, que puede contener datos de texto o de medios.9  
* **Cargas Útiles de Datos (Payloads):** Un objeto Part puede contener datos de tres maneras principales:  
  1. "text": Para prompts de texto simples. El objeto Part contendrá una única clave "text" con una cadena de texto como valor.9  
  2. "inline\_data": Para incrustar datos de medios directamente en la solicitud. Este es un objeto que contiene el mime\_type del archivo (por ejemplo, image/jpeg) y los bytes del medio codificados en Base64 en un campo data.9  
  3. "file\_data": Para hacer referencia a un archivo que ha sido previamente subido a través de la Files API. Este objeto contiene el mime\_type y un file\_uri que apunta al archivo subido.10

Esta estructura flexible permite combinar diferentes tipos de medios y texto en una sola solicitud coherente, formando la base para todas las interacciones multimodales.

## **Sección 2: Análisis de Videos de YouTube Directamente a través de URL**

Una de las capacidades más potentes y simplificadas de la API de Gemini es su habilidad para analizar videos de YouTube directamente desde una URL. Esta funcionalidad aborda directamente la primera parte de la consulta del usuario y representa un cambio significativo en la facilidad con la que se pueden construir aplicaciones de análisis de video.

### **2.1. Soporte Nativo para URLs de YouTube**

La API de Gemini soporta de forma nativa el análisis de videos de YouTube que sean públicos o no listados, simplemente proporcionando la URL del video en la solicitud.12 Esta característica es una abstracción de una complejidad considerable; elimina por completo la necesidad de que los desarrolladores construyan una infraestructura para descargar el video, extraer las pistas de audio y video, y realizar cualquier preprocesamiento.4

Este enfoque consolida lo que tradicionalmente sería un pipeline de múltiples pasos y propenso a errores (que involucraría herramientas como pytube para la descarga y ffmpeg para la extracción) en una única llamada atómica a la API. Esto no es solo una conveniencia, sino un cambio fundamental en la responsabilidad del desarrollador. El enfoque se desplaza de la ingeniería de medios y la gestión de la infraestructura hacia la ingeniería de prompts y la extracción de valor del contenido. Esta democratización del análisis de video permite a los desarrolladores sin experiencia en procesamiento de medios construir aplicaciones sofisticadas.

### **2.2. Implementación: Código y Ejemplos REST**

La implementación de esta característica es notablemente sencilla, tanto con el SDK de Python como con una llamada directa a la API REST.

#### **SDK de Python (google-generativeai)**

El SDK de Python proporciona una abstracción de alto nivel que facilita la inclusión de una URL de YouTube. La función clave es genai.Part.from\_uri(), que toma la URL del video y su tipo MIME (video/mp4) como argumentos.

Python

\# Código basado en \[10\], anotado para mayor claridad  
import google.generativeai as genai

\# Configurar con la clave de API de Google AI Studio  
genai.configure(api\_key="YOUR\_GEMINI\_API\_KEY")

\# Definir el modelo a utilizar (por ejemplo, gemini-1.5-flash)  
model \= genai.GenerativeModel('gemini-1.5-flash') 

\# El prompt incluye tanto la URI del video como la instrucción de texto  
response \= model.generate\_content()

\# Imprimir la respuesta generada por el modelo  
print(response.text)

#### **API REST (cURL)**

Para los desarrolladores que trabajan en entornos sin un SDK dedicado o que desean comprender la estructura subyacente, la llamada REST equivalente a través de cURL es igualmente directa. La URL se pasa dentro de un objeto file\_data.

Bash

\# Comando cURL reconstruido basado en la estructura de \[13\] y \[10\]  
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent" \\  
     \-H "x-goog-api-key: $GEMINI\_API\_KEY" \\  
     \-H 'Content-Type: application/json' \\  
     \-X POST \\  
     \-d '{  
       "contents":  
         }  
       \]  
     }'

### **2.3. Aplicaciones Avanzadas e Ingeniería de Prompts**

La capacidad de analizar videos de YouTube va mucho más allá de la simple generación de resúmenes. Mediante la ingeniería de prompts avanzada, es posible transformar la API de un simple transcriptor a un analista estratégico.

#### **Automatización de Flujos de Trabajo**

Herramientas de automatización como n8n demuestran cómo esta capacidad se puede integrar en flujos de trabajo para generar automáticamente resúmenes, transcripciones completas y extraer información específica basada en prompts dinámicos del usuario.13 Por ejemplo, un flujo de trabajo podría tomar una URL de YouTube, pedir al modelo que identifique "todos los momentos clave con marcas de tiempo" y luego guardar esta información estructurada en una hoja de cálculo.14

#### **Análisis Estratégico con "Super Prompts"**

Las discusiones de la comunidad han dado lugar a la creación de "super prompts" diseñados para extraer el máximo valor de un video. En lugar de una simple pregunta como "resume esto", un prompt más sofisticado puede solicitar un análisis estructurado. El "Gemini Strategic Analyst Prompt" es un excelente ejemplo de esto.15

Ejemplo de Super Prompt de Gemini:  
"Actúa como un analista estratégico de clase mundial utilizando tu extensión nativa de YouTube. Tu análisis debe ser profundo, perspicaz y estructurado para mayor claridad. Para el video enlazado a continuación, por favor proporciona lo siguiente:

* **La Tesis Central:** En una única y concisa oración, ¿cuál es el argumento absolutamente central de este video?  
* **Pilares Clave del Argumento:** Presenta los 3-5 argumentos principales que apoyan la tesis central.  
* **El Gancho Deconstruido:** Cita el gancho de los primeros 30 segundos y explica el disparador psicológico que utiliza (por ejemplo, 'Crea una brecha de información', 'Desafía una creencia común').  
* **Momento Más Tuiteable:** Identifica la cita más poderosa y compartible del video y preséntala como una cita en bloque.  
* Audiencia y Propósito: Describe la audiencia objetivo y el objetivo principal que el creador probablemente tenía (por ejemplo, 'Educar a principiantes', 'Construir afinidad de marca').  
  Analiza este video:".15

Este tipo de prompt dirige al modelo para que vaya más allá de la superficie del contenido y analice su estructura, estrategia y propósito, proporcionando insights de un valor mucho mayor.

## **Sección 3: Procesamiento de Archivos Locales y Remotos (Imágenes, Video y Más)**

Además de las URLs de YouTube, una parte fundamental de la funcionalidad multimodal de Gemini es su capacidad para procesar archivos subidos por el usuario, como imágenes, videos y documentos. La API ofrece dos métodos distintos para enviar estos archivos, y la elección entre ellos es una decisión arquitectónica crítica para cualquier aplicación.

### **3.1. Eligiendo su Método: Datos Inline vs. The Files API**

La decisión principal sobre cómo enviar un archivo se basa en su tamaño y en la frecuencia con la que se reutilizará. La API impone un límite estricto de 20 MB para las solicitudes simples y proporciona una alternativa más compleja pero escalable para archivos más grandes.2 Esta no es simplemente una limitación técnica, sino una elección de diseño deliberada. Un único endpoint síncrono para archivos grandes sería propenso a tiempos de espera y resultaría ineficiente. Al crear una Files API separada, Google guía a los desarrolladores hacia la adopción de un patrón de estilo asíncrono más robusto para el procesamiento de medios pesados. La aplicación debe manejar el estado de "subida" por separado del estado de "análisis", lo que conduce a una arquitectura de aplicación más resiliente y eficiente.

* **Datos Inline (Base64):** Este método es ideal para archivos pequeños, donde el tamaño total de la solicitud (incluyendo el prompt, los bytes de la imagen, etc.) es inferior a 20 MB. Es una opción directa y adecuada para archivos de un solo uso, como avatares de usuario, fotos de productos simples o capturas de pantalla.2  
* **The Files API:** Este método es obligatorio para cualquier solicitud que supere el umbral de 20 MB. Es superior para archivos grandes (videos, imágenes de alta resolución, PDFs largos), archivos que se reutilizarán en múltiples prompts (para ahorrar ancho de banda de subida y costos de procesamiento), y para construir aplicaciones más robustas y escalables.2

La siguiente tabla resume los factores clave a considerar al elegir un método.

| Característica | Datos Inline (Base64) | The Files API |
| :---- | :---- | :---- |
| **Caso de Uso** | Archivos pequeños (\<20 MB), de un solo uso. | Archivos grandes (\>20 MB), reutilizables. |
| **Tamaño Máx. de Solicitud** | 20 MB (total) 2 | 2 GB por archivo 3 |
| **Reutilización de Archivos** | Ineficiente; el archivo debe ser codificado y enviado con cada solicitud. | Alta; subir una vez, hacer referencia varias veces.2 |
| **Complejidad de Implementación** | Baja; un solo paso. | Media; proceso de dos pasos (subir, luego solicitar). |
| **Pasos de API** | 1 (Llamada a generateContent) | 2 (Llamada a files.upload, luego a generateContent) 2 |
| **Persistencia de Archivos** | Ninguna; los datos solo existen durante la solicitud. | 48 horas 3 |

### **3.2. Método 1: Envío de Datos Inline (Codificación Base64)**

Este método implica convertir un archivo binario, como una imagen, en una cadena de texto Base64. Esta cadena se puede incrustar directamente en el cuerpo de la solicitud JSON.9

#### **Concepto**

La codificación Base64 es un estándar para representar datos binarios en un formato de texto ASCII. Esto permite que los archivos se transmitan de forma segura dentro de estructuras de datos basadas en texto como JSON.

#### **Implementación en Python**

El SDK de Python simplifica este proceso. Se puede leer un archivo de imagen local en modo binario y pasarlo directamente a la API, que se encarga de la codificación.

Python

\# Ejemplo de envío de una imagen local como datos inline  
import google.generativeai as genai  
from PIL import Image

genai.configure(api\_key="YOUR\_GEMINI\_API\_KEY")  
model \= genai.GenerativeModel('gemini-1.5-flash')

\# Abrir la imagen usando una biblioteca como Pillow  
img \= Image.open("path/to/your/image.jpg")

\# Enviar la imagen y el prompt al modelo  
response \= model.generate\_content(\["¿Qué hay en esta imagen?", img\])  
print(response.text)

#### **Estructura de la API REST**

En una llamada REST directa, el desarrollador es responsable de codificar el archivo en Base64. La cadena resultante se coloca en el campo data dentro de un objeto inline\_data.

JSON

{  
  "contents":  
  }\]  
}

9

### **3.3. Método 2: The Files API para Medios Grandes o Reutilizables**

Para archivos que superan el límite de 20 MB o que se utilizarán repetidamente, la Files API es la solución correcta. Es un proceso de dos pasos diseñado para la eficiencia y la escalabilidad.2

#### **Concepto y Ciclo de Vida del Archivo**

1. **Subida:** El archivo se sube primero a un almacenamiento temporal gestionado por Google. La API devuelve una referencia (URI) a ese archivo.  
2. **Referencia:** Esta URI se utiliza en una o más llamadas posteriores a generateContent para hacer referencia al archivo subido.

Los archivos subidos a través de la Files API se almacenan durante 48 horas. Hay un límite de almacenamiento de 20 GB por proyecto y un tamaño máximo de archivo de 2 GB.3

#### **Implementación con el SDK de Python**

El SDK de Python gestiona este proceso de dos pasos de forma elegante.

Python

\# Ejemplo completo usando la Files API con Python  
import google.generativeai as genai

genai.configure(api\_key="YOUR\_GEMINI\_API\_KEY")  
model \= genai.GenerativeModel('gemini-1.5-flash')

\# Paso 1: Subir el archivo (puede ser un video grande, PDF, etc.)  
\# El SDK se encarga de la subida y devuelve un objeto de referencia.  
print("Subiendo archivo...")  
video\_file \= genai.upload\_file(path="path/to/large\_video.mp4", display\_name="Mi Video de Demostración")  
print(f"Archivo subido: {video\_file.uri}")

\# Paso 2: Usar el objeto de archivo en una llamada a generate\_content  
print("Generando descripción del video...")  
response \= model.generate\_content()

\# Opcional: Eliminar el archivo después de usarlo si ya no es necesario  
genai.delete\_file(video\_file.name)  
print("Archivo eliminado.")

print("\\nRespuesta del modelo:")  
print(response.text)

2

#### **Flujo de Trabajo de la API REST**

El flujo de trabajo REST es más complejo e implica una solicitud de subida reanudable inicial para obtener una URL de subida, seguida de la subida real de los bytes del archivo a esa URL. Una vez completado, la respuesta contiene el file\_uri que se puede utilizar en la llamada final a generateContent dentro de un objeto file\_data.18 Este proceso, aunque más detallado, proporciona un control granular para aplicaciones robustas.

## **Sección 4: Guía de Referencia: Formatos Soportados y Límites Operativos**

Para construir aplicaciones fiables sobre la API de Gemini, es fundamental conocer las especificaciones técnicas, los formatos de archivo soportados y las limitaciones operativas de cada modelo. Esta sección consolida esta información crítica en tablas de referencia rápida.

### **4.1. Matriz Completa de Soporte de Archivos**

Una de las primeras preguntas que un desarrollador se hace es: "¿Puede Gemini procesar mi tipo de archivo específico?". El envío del mime\_type correcto es esencial para que la API interprete correctamente los datos. La siguiente tabla proporciona una fuente única de verdad para todos los formatos de archivo soportados.

| Categoría | Formatos Soportados y Tipos MIME | Fuentes |
| :---- | :---- | :---- |
| **Imagen** | PNG (image/png), JPEG (image/jpeg), WebP (image/webp) | 12 |
| **Video** | MP4 (video/mp4), MOV (video/quicktime), MPG (video/mpg), MPEG (video/mpeg), FLV (video/x-flv), WEBM (video/webm), WMV (video/wmv), 3GPP (video/3gpp) | 12 |
| **Audio** | MP3 (audio/mp3), WAV (audio/wav), FLAC (audio/flac), AAC (audio/aac), OPUS (audio/opus), M4A (audio/m4a) | 12 |
| **Documento** | PDF (application/pdf), Texto Plano (text/plain) | 12 |

### **4.2. Capacidades y Límites Específicos del Modelo**

No todos los modelos Gemini son iguales. Tienen diferentes capacidades, ventanas de contexto y límites de procesamiento. Un desarrollador puede procesar con éxito un video de 30 minutos con gemini-1.5-pro pero descubrir que falla con un modelo más pequeño. Esta discrepancia subraya que el "soporte" para un formato de archivo es condicional. El verdadero sobre operativo es un espacio multidimensional definido por el formato, la duración, la resolución, la presencia de una pista de audio y el modelo elegido.

Simplemente verificar el soporte del formato es insuficiente para construir una aplicación fiable. Los desarrolladores deben implementar comprobaciones previas o un manejo de errores robusto que tenga en cuenta estas restricciones más profundas y específicas del modelo. Las siguientes tablas son herramientas esenciales para diseñar esta lógica de validación necesaria.

#### **Tabla de Límites Operativos Generales**

| Límite/Característica | Valor | Fuentes |
| :---- | :---- | :---- |
| **Límite de Solicitud Inline** | 20 MB (tamaño total de la solicitud) | 2 |
| **Tamaño Máx. Archivo (Files API)** | 2 GB | 3 |
| **Almacenamiento Total (Files API)** | 20 GB por proyecto | 3 |
| **Persistencia Archivo (Files API)** | 48 horas | 3 |
| **Máx. Imágenes por Prompt** | 3,000 (para modelos Gemini 1.5/2.5) | 20 |
| **Resolución Máx. Imagen** | Escaladas para ajustarse a 3072 x 3072 píxeles | 12 |
| **Ventana de Contexto (Gemini 1.5 Pro)** | 1 millón de tokens (aprox. 1,500 páginas) | 22 |

#### **Tabla de Límites de Procesamiento de Video por Modelo**

| Modelo | Duración Máx. Video (con audio) | Duración Máx. Video (sin audio) | Máx. Videos por Prompt |
| :---- | :---- | :---- | :---- |
| **Gemini 1.5 Pro** | Aprox. 45 minutos | Aprox. 1 hora | 10 |
| **Gemini 1.5 Flash** | Aprox. 45 minutos | Aprox. 1 hora | 10 |
| **Gemini 1.0 Pro** | Aprox. 45 minutos | Aprox. 1 hora | 10 |

Nota: La tabla anterior es una síntesis de los datos de Vertex AI.21 Los límites pueden variar ligeramente entre las implementaciones de AI Studio y Vertex AI.

## **Conclusión: Síntesis de Conocimientos y Exploración de Futuras Fronteras**

### **Resumen de Aprendizajes Clave**

Este informe ha proporcionado una guía exhaustiva para los desarrolladores que utilizan las capacidades multimodales de la API de Gemini. Los puntos más críticos a recordar son:

1. **La Simplicidad del Análisis de YouTube:** La capacidad de analizar videos de YouTube directamente desde una URL es una característica potente que abstrae una complejidad significativa, permitiendo a los desarrolladores centrarse en la extracción de valor a través de la ingeniería de prompts.  
2. **La Decisión Arquitectónica de 20 MB:** La elección entre enviar datos inline (Base64) y usar la Files API es fundamental. El umbral de 20 MB dicta el enfoque, guiando a los desarrolladores hacia arquitecturas de aplicación más robustas y escalables para el manejo de medios grandes.  
3. **La Importancia de las Especificaciones:** El éxito en la implementación depende de una comprensión clara de los formatos de archivo soportados, los tipos MIME correctos y, lo que es más importante, los límites operativos específicos de cada modelo. Las tablas de referencia proporcionadas son herramientas indispensables para diseñar lógica de validación y manejo de errores.

### **Vías para una Mayor Exploración**

Las capacidades de Gemini se extienden más allá de los temas cubiertos en esta guía. Se anima a los desarrolladores a explorar las siguientes funcionalidades avanzadas para desbloquear casos de uso aún más innovadores:

* **Tareas de Visión Avanzadas:** Además de la comprensión general, los modelos Gemini pueden realizar tareas de visión por computadora más específicas, como la detección de objetos y la segmentación, que pueden devolver las coordenadas de las cajas delimitadoras (bounding boxes) para los elementos identificados en una imagen.2  
* **Multimodalidad Generativa:** La API no solo puede analizar medios, sino también generarlos. Modelos como gemini-1.5-flash-image pueden crear imágenes a partir de descripciones de texto, participar en conversaciones de edición de imágenes y generar resultados que intercalan texto e imágenes, como una publicación de blog ilustrada.23  
* **Respuestas en Streaming:** Para aplicaciones interactivas que requieren una retroalimentación en tiempo real, el método streamGenerateContent es crucial. Permite que la respuesta del modelo se transmita al cliente a medida que se genera, mostrando resultados parciales de inmediato y mejorando significativamente la experiencia del usuario.9

Al dominar los fundamentos presentados en esta guía y explorar estas fronteras avanzadas, los desarrolladores están bien equipados para construir la próxima generación de aplicaciones inteligentes e impulsadas por la multimodalidad.

#### **Works cited**

1. Gemini Vision API Guide: AI for Image, Video & Document Processing \- VideoSDK, accessed October 15, 2025, [https://www.videosdk.live/developer-hub/ai/gemini-vision-api](https://www.videosdk.live/developer-hub/ai/gemini-vision-api)  
2. Image understanding | Gemini API | Google AI for Developers, accessed October 15, 2025, [https://ai.google.dev/gemini-api/docs/image-understanding](https://ai.google.dev/gemini-api/docs/image-understanding)  
3. Files API | Gemini API | Google AI for Developers, accessed October 15, 2025, [https://ai.google.dev/gemini-api/docs/files](https://ai.google.dev/gemini-api/docs/files)  
4. Build a Gemini-Powered YouTube Summarizer \- Google Codelabs, accessed October 15, 2025, [https://codelabs.developers.google.com/devsite/codelabs/build-youtube-summarizer](https://codelabs.developers.google.com/devsite/codelabs/build-youtube-summarizer)  
5. 7 examples of Gemini's multimodal capabilities in action \- Google Developers Blog, accessed October 15, 2025, [https://developers.googleblog.com/en/7-examples-of-geminis-multimodal-capabilities-in-action/](https://developers.googleblog.com/en/7-examples-of-geminis-multimodal-capabilities-in-action/)  
6. How To Set Up FREE AI Video Analysis Using N8N And Google Gemini \- AI Fire, accessed October 15, 2025, [https://www.aifire.co/p/how-to-set-up-free-ai-video-analysis-using-n8n-and-google-gemini](https://www.aifire.co/p/how-to-set-up-free-ai-video-analysis-using-n8n-and-google-gemini)  
7. Gemini API in Vertex AI quickstart \- Google Cloud, accessed October 15, 2025, [https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart)  
8. Video Intelligence API documentation | Google Cloud, accessed October 15, 2025, [https://cloud.google.com/video-intelligence/docs](https://cloud.google.com/video-intelligence/docs)  
9. Gemini API reference | Google AI for Developers, accessed October 15, 2025, [https://ai.google.dev/api](https://ai.google.dev/api)  
10. Use Gemini to summarize YouTube videos | Generative AI on Vertex ..., accessed October 15, 2025, [https://cloud.google.com/vertex-ai/generative-ai/docs/samples/googlegenaisdk-textgen-with-youtube-video](https://cloud.google.com/vertex-ai/generative-ai/docs/samples/googlegenaisdk-textgen-with-youtube-video)  
11. Image and Video Processing using Google Gemini LLM | by sai harish cherukuri \- Medium, accessed October 15, 2025, [https://saiharishcherukuri.medium.com/image-and-video-processing-using-google-gemini-llm-795787784b23](https://saiharishcherukuri.medium.com/image-and-video-processing-using-google-gemini-llm-795787784b23)  
12. Supported input files and requirements | Firebase AI Logic \- Google, accessed October 15, 2025, [https://firebase.google.com/docs/ai-logic/input-file-requirements](https://firebase.google.com/docs/ai-logic/input-file-requirements)  
13. YouTube Video Content Analyzer & Summarizer with Gemini AI | n8n workflow template, accessed October 15, 2025, [https://n8n.io/workflows/6152-youtube-video-content-analyzer-and-summarizer-with-gemini-ai/](https://n8n.io/workflows/6152-youtube-video-content-analyzer-and-summarizer-with-gemini-ai/)  
14. Analyze YouTube Video for Summaries, Transcripts & Content \+ Google Gemini AI \- N8N, accessed October 15, 2025, [https://n8n.io/workflows/3289-analyze-youtube-video-for-summaries-transcripts-and-content-google-gemini-ai/](https://n8n.io/workflows/3289-analyze-youtube-video-for-summaries-transcripts-and-content-google-gemini-ai/)  
15. I used this Gemini prompt and the Gemini API to analyzed 10,000+ YouTube Videos in 24 hours. Here's the knowledge extraction system that changed how I learn forever : r/GeminiAI \- Reddit, accessed October 15, 2025, [https://www.reddit.com/r/GeminiAI/comments/1m8bf7k/i\_used\_this\_gemini\_prompt\_and\_the\_gemini\_api\_to/](https://www.reddit.com/r/GeminiAI/comments/1m8bf7k/i_used_this_gemini_prompt_and_the_gemini_api_to/)  
16. Video understanding | Gemini API | Google AI for Developers, accessed October 15, 2025, [https://ai.google.dev/gemini-api/docs/video-understanding](https://ai.google.dev/gemini-api/docs/video-understanding)  
17. How to Input Image in Gemini AI API Python Latest Tutorial \- YouTube, accessed October 15, 2025, [https://www.youtube.com/watch?v=WSnSJD1fOXA](https://www.youtube.com/watch?v=WSnSJD1fOXA)  
18. Using files | Gemini API \- Google AI for Developers, accessed October 15, 2025, [https://ai.google.dev/api/files](https://ai.google.dev/api/files)  
19. How Can I Send Files to Google's Gemini Models via API Call? \- Stack Overflow, accessed October 15, 2025, [https://stackoverflow.com/questions/77758177/how-can-i-send-files-to-googles-gemini-models-via-api-call](https://stackoverflow.com/questions/77758177/how-can-i-send-files-to-googles-gemini-models-via-api-call)  
20. Image understanding | Generative AI on Vertex AI \- Google Cloud, accessed October 15, 2025, [https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-understanding](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-understanding)  
21. Video understanding | Generative AI on Vertex AI | Google Cloud, accessed October 15, 2025, [https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding)  
22. What is the usage limit of gemini advanced 2.5 pro?(not api\!) \- Google Help, accessed October 15, 2025, [https://support.google.com/gemini/thread/341614088/what-is-the-usage-limit-of-gemini-advanced-2-5-pro-not-api?hl=en](https://support.google.com/gemini/thread/341614088/what-is-the-usage-limit-of-gemini-advanced-2-5-pro-not-api?hl=en)  
23. Generate images with Gemini | Generative AI on Vertex AI \- Google Cloud, accessed October 15, 2025, [https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-generation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-generation)  
24. Analyze video files using the Gemini API | Firebase AI Logic \- Google, accessed October 15, 2025, [https://firebase.google.com/docs/ai-logic/analyze-video](https://firebase.google.com/docs/ai-logic/analyze-video)