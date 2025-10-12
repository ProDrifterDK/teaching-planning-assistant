

# **Arquitectura de Datos para el Currículum Nacional de Chile: El Blueprint Definitivo**

## **Introducción: De Documentos No Estructurados a Inteligencia Accionable**

### **Propósito del Informe**

Este documento constituye el plan maestro arquitectónico para transformar el Currículum Nacional de Chile desde una colección de documentos dispares a un modelo de datos unificado, relacional y legible por máquina. Fusiona un análisis conceptual de alto nivel con una guía de implementación práctica, refinada a través del examen de documentos curriculares reales. Está diseñado para guiar un sofisticado proceso de extracción y estructuración de datos que aprovecha los Modelos de Lenguaje Grandes (LLM).

### **El Desafío Central**

El currículum oficial, difundido a través de plataformas como curriculumnacional.cl y la bibliotecadigital.mineduc.cl, existe principalmente en formatos legibles por humanos (páginas web, documentos PDF) sin una API pública para el acceso programático.1 El análisis de documentos fuente, como las *Bases Curriculares*, revela matices cruciales: los Objetivos de Aprendizaje (OA) están numerados secuencialmente y carecen de códigos alfanuméricos, mientras que los Ejes y Actitudes se definen a un nivel superior, aplicándose a grupos de OA.4 Esta situación valida la necesidad de un enfoque de IA, pero exige una estrategia de extracción sofisticada que pueda interpretar el contexto y la estructura implícita de los documentos.

### **El Objetivo Estratégico**

El objetivo es crear una "única fuente de verdad" que no solo capture la estructura jerárquica del currículum, sino también su naturaleza dinámica, relacional y temporal. Estos datos estructurados serán la base para aplicaciones educativas de próxima generación, como la herramienta de planificación docente que propones, permitiendo un nivel de análisis y personalización actualmente inalcanzable.

---

## **I. La Arquitectura Fundacional: Un Modelo de Datos Relacional para el Currículum Chileno**

Esta sección define el esquema a nivel macro, estableciendo las entidades centrales que forman la columna vertebral del currículum. El modelo debe ser lo suficientemente robusto para manejar las diversas modalidades educativas y los tipos de documentos que componen el ecosistema curricular.

### **1.1. El Marco Legal y Conceptual: Comprendiendo el Ecosistema**

El currículum chileno está mandatado por la Ley General de Educación (LGE), que reemplazó a la anterior Ley Orgánica Constitucional de Enseñanza (LOCE).6 La LGE ordena la creación de las *Bases Curriculares*, que establecen los aprendizajes mínimos para todos los estudiantes del país.4 El Ministerio de Educación (Mineduc), a través de su Unidad de Currículum y Evaluación (UCE), es el principal autor y custodio de estos documentos.7

La diseminación de esta información se realiza a través de un sistema dual:

1. **Portal de Servicio (curriculumnacional.cl):** Ofrece una vista navegable y amigable, presentando la jerarquía del currículum de manera clara: Nivel Educativo \> Curso \> Asignatura.9 Funciona como un mapa conceptual para el uso diario de los docentes.  
2. **Repositorio de Archivo (bibliotecadigital.mineduc.cl):** Actúa como el archivo oficial de los documentos fuente, principalmente en formato PDF.3 Proporciona los documentos autoritativos, pero con una lógica de biblioteca digital.

Un proceso de extracción de datos robusto debe utilizar ambas fuentes. El portal web proporciona el "mapa" de la estructura, mientras que la biblioteca digital proporciona el "territorio" oficial. Por lo tanto, el modelo de datos debe incorporar una entidad DocumentoFuente para rastrear la procedencia de cada pieza de información, garantizando integridad y auditabilidad.

### **1.2. Entidades Jerárquicas Centrales: La Columna Vertebral del Currículum**

El modelo de datos se construirá en torno a una jerarquía clara, reflejando la estructura presentada en los portales del Mineduc.9

* **ModalidadEducativa:** La entidad de más alto nivel. Ejemplos: 'Educación General', 'Formación Diferenciada Técnico-Profesional', 'Educación de Personas Jóvenes y Adultas (EPJA)'.9  
* **NivelEducativo:** Las principales etapas de la escolaridad. Ejemplos: 'Educación Básica', 'Educación Media'.6  
* **Curso:** El grado específico. Ejemplos: '1° Básico', '7° Básico'.  
* **Asignatura:** La materia específica. Ejemplos: 'Matemática', 'Lengua y Literatura'.  
* **EjeCurricular:** Áreas temáticas dentro de una asignatura. Ejemplos para Matemática: 'Números y Operaciones', 'Geometría'.11  
* **Actitud:** Disposiciones generales para una asignatura. El análisis de las *Bases Curriculares* muestra que se definen a nivel de asignatura, no por OA individual.

### **1.3. Entidad de Tipología de Documentos: Categorizando el Material Fuente**

Se requiere una entidad TipoDocumento para clasificar los archivos de origen, ya que cada uno cumple una función distinta:

* **Bases Curriculares:** Definen el "qué" (los OA obligatorios).4  
* **Programas de Estudio:** Detallan el "cómo" (orientaciones didácticas).13  
* **Planes de Estudio:** Definen el "cuándo" (distribución del tiempo).15  
* **Mapas de Progreso / Progresiones de Aprendizaje:** Describen la "trayectoria" del aprendizaje a lo largo del tiempo.  
* **Documentos de Priorización:** Superposiciones temporales que modifican el currículum base.

### **Tabla 1: Entidades Centrales y sus Atributos Primarios**

| Nombre de la Entidad | Atributos Primarios | Descripción | Ejemplo |
| :---- | :---- | :---- | :---- |
| DocumentoFuente | doc\_id (PK), url, titulo, fecha\_publicacion, autor, hash\_contenido, tipo\_doc\_id (FK) | Representa un único archivo fuente (PDF, página web). | 'Bases Curriculares 7° a 2° medio.pdf' |
| ModalidadEducativa | modalidad\_id (PK), nombre | La trayectoria educativa. | 'Formación Diferenciada Técnico-Profesional' |
| NivelEducativo | nivel\_id (PK), nombre, modalidad\_id (FK) | La etapa educativa. | 'Educación Básica' |
| Curso | curso\_id (PK), nombre, nivel\_id (FK) | Un grado o nivel específico. | '7° Básico' |
| Asignatura | asignatura\_id (PK), nombre | Una materia específica. | 'Lengua y Literatura' |
| Actitud | actitud\_id (PK), letra\_actitud, texto\_actitud, asignatura\_id (FK) | Una disposición a ser desarrollada en la asignatura. | (A, 'Manifestar disposición a formarse un pensamiento propio...') |
| EjeCurricular | eje\_id (PK), nombre, asignatura\_id (FK) | Una hebra temática dentro de una asignatura. | 'Lectura' |

---

## **II. Deconstruyendo el "Objetivo de Aprendizaje": La Unidad Atómica del Currículum**

Esta sección proporciona un esquema detallado para el elemento más granular y central del currículum: el *Objetivo de Aprendizaje (OA)*. Estructurar esta entidad correctamente es de suma importancia para el éxito del proyecto.

### **2.1. La Anatomía de un OA: Atributos Centrales y la Tríada del Aprendizaje**

El OA es la unidad fundamental de aprendizaje definida en las *Bases Curriculares*.4 Su formulación integra explícitamente **conocimientos, habilidades y actitudes**, conformando un currículum centrado en el aprendizaje del estudiante.4

El análisis del documento de 7° Básico revela que el oa\_codigo (ej. 'LE07 OA 03') no está presente en el texto de las *Bases Curriculares*. En su lugar, se utiliza una numeración secuencial simple. Esto requiere un ajuste crucial en nuestra entidad principal.

* **Entidad ObjetivoAprendizaje (Revisada):**  
  * oa\_id (PK): Identificador único interno.  
  * numero\_oa (INT): El número secuencial dentro del documento (ej. 1, 2,..., 25).  
  * texto\_oa: El texto completo del objetivo.  
  * desglose\_componentes (JSON o TEXT): Un campo para almacenar de forma estructurada los sub-puntos o viñetas que detallan el OA (ej. los 6 puntos del OA 3 de Lenguaje 7° Básico).  
  * eje\_id (FK): Vínculo al eje curricular.  
  * curso\_id (FK): Vínculo al curso.  
  * doc\_fuente\_id (FK): Vínculo al documento de origen.  
  * oa\_codigo\_oficial (VARCHAR, NULABLE): **Campo clave**. Estará inicialmente vacío y se llenará en una fase posterior de "enriquecimiento" al cruzar los datos con otras fuentes (como curriculumnacional.cl) que sí utilizan el código oficial.

### **2.2. Enriquecimiento Pedagógico: Datos de los *Programas de Estudio***

Los *Programas de Estudio* son la fuente principal de información práctica para cada OA.13 Son indispensables para dar vida al currículum y deben ser modelados como entidades directamente relacionadas con el OA, utilizando el oa\_codigo\_oficial como clave de enlace.

* **IndicadorEvaluacion:** Comportamientos concretos y observables que demuestran el logro de un OA. La relación es de uno a muchos: un OA tiene múltiples indicadores.  
  * indicador\_id (PK), texto\_indicador, oa\_id (FK).  
* **ActividadSugerida:** Ejemplos de actividades de aula que ayudan a enseñar el OA. La relación también es de uno a muchos.  
  * actividad\_id (PK), descripcion\_actividad, oa\_id (FK).

### **Tabla 2: Esquema Detallado para la Entidad ObjetivoAprendizaje y sus Sub-Entidades Vinculadas**

| Nombre de la Tabla | Nombre del Campo | Tipo de Dato | Restricciones | Descripción |
| :---- | :---- | :---- | :---- | :---- |
| ObjetivoAprendizaje | oa\_id | INT | PK, AUTO\_INCREMENT | ID interno único. |
|  | numero\_oa | INT | NOT NULL | Número secuencial en el documento (1, 2, 3...). |
|  | texto\_oa | TEXT | NOT NULL | Texto principal del objetivo. |
|  | desglose\_componentes | JSON | NULLABLE | Array con los textos de los sub-puntos o viñetas. |
|  | eje\_id | INT | FK a EjeCurricular | Vínculo al eje curricular. |
|  | doc\_fuente\_id | INT | FK a DocumentoFuente | Vínculo al documento fuente. |
|  | oa\_codigo\_oficial | VARCHAR(20) | NULLABLE, UNIQUE | Código oficial del Mineduc (ej. 'LE07 OA 03'), a ser llenado posteriormente. |
| IndicadorEvaluacion | indicador\_id | INT | PK, AUTO\_INCREMENT | ID interno único. |
|  | texto\_indicador | TEXT | NOT NULL | Texto del indicador de evaluación. |
|  | oa\_id | INT | FK a ObjetivoAprendizaje | Vincula el indicador a su OA. |
| ActividadSugerida | actividad\_id | INT | PK, AUTO\_INCREMENT | ID interno único. |
|  | descripcion | TEXT | NOT NULL | Descripción de la actividad sugerida. |
|  | oa\_id | INT | FK a ObjetivoAprendizaje | Vincula la actividad a su OA. |

---

## **III. Capturando las Dinámicas Curriculares: Estructuración de Progresiones y Priorizaciones**

Un modelo estático del currículum es incompleto. Esta sección aborda cómo modelar las relaciones entre los OA a lo largo del tiempo y cómo manejar modificaciones temporales como la *Priorización Curricular*.

### **3.1. Modelando las Trayectorias de Aprendizaje: *Mapas de Progreso* y *Progresiones de Aprendizaje***

El Mineduc proporciona documentos que describen la "secuencia típica" del aprendizaje, conocidos como *Mapas de Progreso* o *Progresiones de Aprendizaje*. Estos documentos organizan el aprendizaje en niveles que describen desempeños cada vez más complejos a lo largo de la trayectoria escolar.17

Sin embargo, estos documentos presentan un desafío: la progresión es a menudo **implícita**. Describen los niveles de aprendizaje con texto detallado, pero no enumeran explícitamente los códigos de los OA que corresponden a cada nivel.18 Aquí es donde un LLM puede aportar un valor inmenso, utilizando técnicas de similitud semántica para inferir y establecer las conexiones más probables entre los OA y los niveles de progresión.

### **3.2. Esquema para las Progresiones de Aprendizaje**

* **MapaProgreso:** mapa\_id (PK), nombre (ej. 'Mapa de Progreso de Lectura'), asignatura\_id (FK).  
* **NivelProgreso:** nivel\_id (PK), mapa\_id (FK), nivel\_num, descripcion\_nivel.  
* **OA\_NivelProgreso:** Una tabla de unión (oa\_id, nivel\_id, confidence\_score) para almacenar las relaciones inferidas. La inclusión de un confidence\_score (puntuación de confianza) es fundamental para registrar la naturaleza probabilística del mapeo.

### **3.3. Modelando Adaptaciones Contextuales: La *Priorización Curricular***

En respuesta a eventos como la pandemia, el Mineduc introdujo una *Priorización Curricular* (vigente para 2023-2025). Esta es una capa de metadatos temporal pero esencial, que clasifica los OA en categorías como **Aprendizajes Basales** y **Aprendizajes Complementarios**.

* **Priorizacion:** priorizacion\_id (PK), nombre (ej. 'Priorización Curricular 2023-2025'), fecha\_inicio, fecha\_fin.  
* **OA\_Priorizacion:** Una tabla de unión (oa\_id, priorizacion\_id, categoria), donde categoria sería un tipo enumerado ('Basal', 'Complementario').

---

## **IV. Hoja de Ruta para la Implementación: Una Guía Práctica para la Extracción de Datos Impulsada por IA**

Esta sección proporciona un plan accionable y por fases para ejecutar la estrategia propuesta, con un enfoque en la ingeniería de prompts para el LLM.

### **4.1. Fase 1: Ensamblaje del Corpus y Pre-procesamiento**

* **Rastreo Sistemático:** Desarrollar scripts para rastrear curriculumnacional.cl y mapear la estructura del currículum, y para descargar sistemáticamente los documentos PDF autoritativos desde bibliotecadigital.mineduc.cl.9  
* **Extracción de Texto de PDF:** Utilizar una biblioteca robusta para extraer el texto, esforzándose por preservar la mayor cantidad de información estructural posible (encabezados, tablas, listas).  
* **Segmentación y Etiquetado:** Segmentar cada documento lógicamente (por capítulo o sección) y etiquetar cada segmento con los metadatos de su DocumentoFuente.

### **4.2. Fase 2: Estructuración Impulsada por IA (Estrategia de Prompting Revisada)**

Adoptamos un enfoque de "cadena de extracción" en múltiples pasos, que es más resiliente y preciso.

* **Paso 1: Prompt de Contexto de Asignatura.**  
  * *Objetivo:* Extraer la información de alto nivel (Ejes, Actitudes) que se aplica a toda la asignatura.  
  * *Input:* Las primeras páginas de la sección de la asignatura en el documento de *Bases Curriculares*.  
  * *Fragmento de Prompt:* "Actúas como un experto en currículum chileno. Analiza el siguiente texto introductorio. Extrae en formato JSON: la Asignatura, los Cursos a los que aplica, una lista de Ejes Curriculares y una lista de Actitudes (con su letra y texto completo)."  
* **Paso 2: Prompt de Extracción de OA por Eje.**  
  * *Objetivo:* Iterar a través del texto y extraer cada OA, asociándolo con su eje y estructurando sus componentes internos.  
  * *Input:* El texto completo de la sección de Objetivos de Aprendizaje.  
  * *Fragmento de Prompt:* "Dado el contexto de Asignatura: Lengua y Literatura y Curso: 7° Básico, procesa el siguiente texto. Identifica los encabezados que actúan como Ejes Curriculares. Para cada objetivo numerado, extrae su numero\_oa, su texto\_oa principal, y cualquier sub-punto como un array en desglose\_componentes. Asocia cada OA con el último Eje Curricular encontrado. Genera una lista de objetos JSON, uno por cada OA."

### **4.3. Fase 3: Validación y Enriquecimiento**

Esta fase es fundamental para completar el conjunto de datos.

* **Validación de Consistencia:** Verificar que todos los OAs fueron extraídos y asociados correctamente a sus ejes.  
* **Enriquecimiento con Códigos Oficiales:** Desarrollar un proceso para mapear los OAs extraídos a sus códigos oficiales. Esto se puede lograr buscando el texto\_oa en el portal curriculumnacional.cl para encontrar el código correspondiente (ej. "LE07 OA 03") y luego poblar el campo oa\_codigo\_oficial en la base de datos.  
* **Humano-en-el-Bucle (Human-in-the-Loop):** Implementar una interfaz de revisión para que un experto humano pueda verificar muestras de la salida de la IA, especialmente para interpretaciones matizadas.

### **Tabla 3: Esquema JSON de Ejemplo y Plantilla de Prompt para la IA**

JSON

// Esquema JSON de Destino (Ejemplo para OA \#3 de Lengua y Literatura 7°)  
// Generado por el Prompt del Paso 2  
{  
  "numero\_oa": 3,  
  "eje\_curricular": "Lectura",  
  "texto\_oa": "Analizar las narraciones leídas para enriquecer su comprensión, considerando, cuando sea pertinente:",  
  "desglose\_componentes": \[  
    "El o los conflictos de la historia.",  
    "El papel que juega cada personaje en el conflicto y cómo sus acciones afectan a otros personajes.",  
    "El efecto de ciertas acciones en el desarrollo de la historia.",  
    "Cuándo habla el narrador y cuándo hablan los personajes.",  
    "La disposición temporal de los hechos.",  
    "Elementos en común con otros textos leídos en el año."  
  \]  
}

Plaintext

// Plantilla de Prompt Revisada (Paso 2\)

Actúas como un especialista en extracción de datos curriculares del Mineduc.  
El contexto actual es:  
\- Asignatura: "Lengua y Literatura"  
\- Curso: "7° Básico"

Procesa el siguiente texto que contiene una lista de Objetivos de Aprendizaje. Tu tarea es:  
1\.  Identificar los encabezados que funcionan como "Ejes Curriculares" (ej. "Escritura", "Comunicación oral"). Mantén el eje actual en memoria.  
2\.  Para cada objetivo numerado, crea un objeto JSON.  
3\.  En cada objeto, extrae:  
    \- "numero\_oa": El número entero del objetivo.  
    \- "eje\_curricular": El último eje que identificaste.  
    \- "texto\_oa": El texto principal del objetivo.  
    \- "desglose\_componentes": Si el objetivo tiene una lista de sub-puntos o viñetas, extráelos como un array de strings. Si no tiene, este campo debe ser nulo.

Genera como salida una lista de estos objetos JSON. No incluyas explicaciones fuera de la lista JSON.

... (pegar aquí el texto de los OA 1 al 25)...

---

## **V. Conclusión: El Potencial Desbloqueado de un Currículum Estructurado**

### **Resumen del Enfoque Arquitectónico**

El modelo relacional propuesto ofrece una solución robusta y escalable para estructurar el Currículum Nacional de Chile. Su diseño captura no solo la jerarquía estática, sino también sus dinámicas complejas. Al tratar la procedencia de los datos como un principio fundamental y al diseñar un esquema que separa las capas curriculares (base, pedagógica, temporal), se establece una base de datos resiliente y preparada para el futuro.

### **Habilitando Innovaciones Futuras**

La creación de este conjunto de datos estructurados es un paso transformador que habilita una nueva generación de herramientas y análisis educativos:

* **Plataformas de Aprendizaje Personalizado:** Permitirán crear rutas de aprendizaje adaptadas, navegando por el grafo de relaciones entre OA.  
* **Herramientas de Apoyo Docente:** Podrán generar automáticamente planes de lecciones, extrayendo OA, indicadores y actividades, liberando tiempo valioso para los educadores.  
* **Análisis Curricular:** Facilitarán el estudio de la evolución del currículum, la identificación de brechas y la comparación con estándares internacionales.

### **Recomendaciones Finales**

Se recomienda enfáticamente adoptar un enfoque iterativo. El currículum es un documento vivo, sujeto a revisiones y actualizaciones continuas por parte del Ministerio de Educación. El sistema de datos debe ser diseñado para incorporar estas futuras actualizaciones de manera eficiente, asegurando que siga siendo una fuente de verdad precisa y relevante a lo largo del tiempo.

#### **Works cited**

1. Portal Currículum Nacional \- Newtenberg, accessed October 11, 2025, [https://www.newtenberg.com/Clientes/Principales/Ministerio-de-Educacion-MINEDUC/104500:Portal-Curriculum-Nacional](https://www.newtenberg.com/Clientes/Principales/Ministerio-de-Educacion-MINEDUC/104500:Portal-Curriculum-Nacional)  
2. Currículum Nacional renueva su web incluyendo una nueva herramienta de apoyo a la Integración Curricular \- Subsecretaría de Educación, accessed October 11, 2025, [https://subeduc.mineduc.cl/curriculum-nacional-renueva-su-web-incluyendo-una-nueva-herramienta-de-apoyo-a-la-integracion-curricular/](https://subeduc.mineduc.cl/curriculum-nacional-renueva-su-web-incluyendo-una-nueva-herramienta-de-apoyo-a-la-integracion-curricular/)  
3. Biblioteca Digital Mineduc \- Ministerio de Educación, accessed October 11, 2025, [https://bibliotecadigital.mineduc.cl/](https://bibliotecadigital.mineduc.cl/)  
4. Bases Curriculares \- Educación Básica \- archivos de www ..., accessed October 11, 2025, [https://archivos.agenciaeducacion.cl/biblioteca\_digital\_historica/orientacion/2012/bases\_curricularesbasica\_2012.pdf](https://archivos.agenciaeducacion.cl/biblioteca_digital_historica/orientacion/2012/bases_curricularesbasica_2012.pdf)  
5. Bases Curriculares \- Educación Media, accessed October 11, 2025, [https://media.mineduc.cl/wp-content/uploads/sites/28/2017/07/Bases-Curriculares-7%C2%BA-b%C3%A1sico-a-2%C2%BA-medio.pdf](https://media.mineduc.cl/wp-content/uploads/sites/28/2017/07/Bases-Curriculares-7%C2%BA-b%C3%A1sico-a-2%C2%BA-medio.pdf)  
6. Curriculum escolar en Chile \- Wikipedia, la enciclopedia libre, accessed October 11, 2025, [https://es.wikipedia.org/wiki/Curriculum\_escolar\_en\_Chile](https://es.wikipedia.org/wiki/Curriculum_escolar_en_Chile)  
7. 4.1. Currículum vigente \- Biblioteca Digital Mineduc, accessed October 11, 2025, [https://bibliotecadigital.mineduc.cl/handle/20.500.12365/36](https://bibliotecadigital.mineduc.cl/handle/20.500.12365/36)  
8. Progresión de Objetivos de Aprendizajes Priorizados. Lenguaje y Comunicación, Lengua y Literatura. \- Biblioteca Digital Mineduc \- Ministerio de Educación, accessed October 11, 2025, [https://bibliotecadigital.mineduc.cl/handle/20.500.12365/14620](https://bibliotecadigital.mineduc.cl/handle/20.500.12365/14620)  
9. Currículum Nacional | Currículum Nacional, accessed October 11, 2025, [https://www.curriculumnacional.cl/](https://www.curriculumnacional.cl/)  
10. Educación de Personas Jóvenes y Adultas, accessed October 11, 2025, [https://epja.mineduc.cl/](https://epja.mineduc.cl/)  
11. Matemática 5° Básico \- Currículum Nacional, accessed October 11, 2025, [https://www.curriculumnacional.cl/curriculum/1o-6o-basico/matematica/5-basico](https://www.curriculumnacional.cl/curriculum/1o-6o-basico/matematica/5-basico)  
12. Curriculum Nacional Chile | PDF | Plan de estudios | Evaluación \- Scribd, accessed October 11, 2025, [https://es.scribd.com/document/414684018/Curriculum-Nacional-Chile](https://es.scribd.com/document/414684018/Curriculum-Nacional-Chile)  
13. Currículo escolar de Chile: génesis, implementación y desarrollo. | MAPEAL, accessed October 11, 2025, [https://mapeal.cippec.org/wp-content/uploads/2014/06/Curr%C3%ADculo-escolar-de-Chile-g%C3%A9nesis-implementaci%C3%B3n-y-desarrollo.pdf](https://mapeal.cippec.org/wp-content/uploads/2014/06/Curr%C3%ADculo-escolar-de-Chile-g%C3%A9nesis-implementaci%C3%B3n-y-desarrollo.pdf)  
14. I. Orientaciones para la comprensión del currículum nacional: enfoque e instrumentos \- Liderazgo Educativo, accessed October 11, 2025, [https://liderazgoeducativo.mineduc.cl/wp-content/uploads/sites/55/2016/04/I.-Orientaciones-para-la-comprensi%C3%B3n-del-curriculum.pdf](https://liderazgoeducativo.mineduc.cl/wp-content/uploads/sites/55/2016/04/I.-Orientaciones-para-la-comprensi%C3%B3n-del-curriculum.pdf)  
15. Planes de estudio \- Curriculum Nacional. MINEDUC. Chile., accessed October 11, 2025, [https://www.curriculumnacional.cl/614/w3-propertyvalue-120182.html](https://www.curriculumnacional.cl/614/w3-propertyvalue-120182.html)  
16. Bases Curriculares \- Currículum Nacional, accessed October 11, 2025, [https://www.curriculumnacional.cl/614/articles-22394\_bases.pdf](https://www.curriculumnacional.cl/614/articles-22394_bases.pdf)  
17. Orientaciones para el uso de los Mapas de Progreso del Aprendizaje \- archivos de www.agenciaeducacion.cl, accessed October 11, 2025, [https://archivos.agenciaeducacion.cl/biblioteca\_digital\_historica/orientacion/2007/orien\_mapas\_simce\_2007.pdf](https://archivos.agenciaeducacion.cl/biblioteca_digital_historica/orientacion/2007/orien_mapas_simce_2007.pdf)  
18. Mapas de Progreso del Aprendizaje \- Biblioteca Digital Mineduc, accessed October 11, 2025, [https://bibliotecadigital.mineduc.cl/bitstream/handle/20.500.12365/14929/mapaprogresomateria.pdf?sequence=1\&isAllowed=y](https://bibliotecadigital.mineduc.cl/bitstream/handle/20.500.12365/14929/mapaprogresomateria.pdf?sequence=1&isAllowed=y)  
19. Progresión de Priorización Curricular | Matemática \- Biblioteca ..., accessed October 11, 2025, [https://bibliotecadigital.mineduc.cl/bitstream/handle/20.500.12365/14619/prog\_OAprior\_Mat.pdf?sequence=1\&isAllowed=y](https://bibliotecadigital.mineduc.cl/bitstream/handle/20.500.12365/14619/prog_OAprior_Mat.pdf?sequence=1&isAllowed=y)