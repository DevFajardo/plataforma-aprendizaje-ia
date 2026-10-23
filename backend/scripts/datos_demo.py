"""Contenido educativo escrito a mano para los datos de demostración (Sprint 9). Sin IA.

Cada cuestionario tiene 8 preguntas (5 de opción múltiple, 2 de verdadero/falso y 1 abierta) con resultado de
aprendizaje (RA), nivel de Bloom, explicación y marca de tiempo. Las transcripciones son RESÚMENES breves escritos
para la demo y coherentes con las preguntas; no son la transcripción literal del video de YouTube.

Cada pregunta: (tipo, enunciado, opciones, correcta, explicación, marca, RA, bloom, dificultad, discriminación)
- dificultad: en logits (negativo = fácil, positivo = difícil) para simular las respuestas de los estudiantes.
- discriminación: 1,0 normal; negativa = ítem defectuoso (lo detecta el análisis de ítems).
"""

VF = ["Verdadero", "Falso"]

# ---------------------------------------------------------------- 1. Modelo relacional
Q1 = {
    "clave": "relacional",
    "titulo": "Bases de datos relacionales: tablas, claves y SQL básico",
    "resumen": (
        "El modelo relacional, propuesto por Edgar F. Codd en 1970, organiza los datos en tablas (relaciones) formadas por "
        "filas (tuplas) y columnas (atributos). La clave primaria identifica cada fila y la clave foránea relaciona tablas; "
        "la integridad referencial evita registros huérfanos. SQL permite consultar con SELECT, FROM y WHERE, y combinar "
        "tablas con JOIN."
    ),
    "ideas_clave": [
        "Los datos se organizan en tablas con filas (tuplas) y columnas (atributos).",
        "La clave primaria identifica de forma única cada fila; no se repite ni es nula.",
        "La clave foránea referencia la clave primaria de otra tabla y las relaciona.",
        "La integridad referencial garantiza que toda clave foránea apunte a una fila existente.",
        "SQL consulta con SELECT, FROM y WHERE; JOIN combina tablas (INNER y LEFT).",
    ],
    "video": {"youtube_id": "pDR5hRfR3g0", "titulo": "MODELO RELACIONAL - CONCEPTOS BASICOS 1"},
    "transcripcion": [
        (0, "Bienvenidos. Hoy veremos los conceptos básicos del modelo relacional, propuesto por Edgar Codd en 1970."),
        (45, "En este modelo los datos se organizan en relaciones, que se representan como tablas formadas por filas y columnas."),
        (90, "Cada fila se llama tupla o registro y representa una instancia de la entidad, por ejemplo un estudiante; cada columna es un atributo con un dominio, es decir, el conjunto de valores permitidos."),
        (140, "La clave primaria identifica de forma única cada fila de la tabla; no puede repetirse ni ser nula."),
        (190, "La clave foránea es un atributo que referencia la clave primaria de otra tabla y permite relacionar ambas tablas."),
        (240, "La integridad referencial garantiza que una clave foránea siempre apunte a una fila existente: no se puede registrar un pedido de un cliente que no existe."),
        (290, "SQL es el lenguaje estándar para consultar: SELECT elige las columnas, FROM indica la tabla y WHERE filtra las filas."),
        (340, "Para combinar tablas usamos JOIN: INNER JOIN devuelve solo las filas que coinciden en ambas tablas y LEFT JOIN conserva todas las filas de la tabla izquierda."),
        (390, "En resumen, tablas, claves, integridad y SQL son la base de cualquier sistema relacional como MySQL, PostgreSQL o SQLite."),
    ],
    "preguntas": [
        ("opcion_multiple", "¿Quién propuso el modelo relacional de bases de datos?",
         ["Edgar F. Codd", "Peter Chen", "Charles Bachman", "Donald Knuth"], "Edgar F. Codd",
         "Edgar F. Codd presentó el modelo relacional en 1970; Peter Chen propuso después el modelo entidad-relación.",
         "00:00", "RA4", "recordar", -1.4, 1.0),
        ("opcion_multiple", "En el modelo relacional, ¿qué representa una fila (tupla) de una tabla?",
         ["Una instancia concreta de la entidad, por ejemplo un estudiante", "El conjunto de valores permitidos de un atributo",
          "La clave que relaciona dos tablas", "El nombre de la tabla"],
         "Una instancia concreta de la entidad, por ejemplo un estudiante",
         "Cada fila es un registro; el conjunto de valores permitidos de una columna es su dominio.",
         "01:30", "RA4", "comprender", -0.8, 1.0),
        ("verdadero_falso", "Una clave primaria puede contener valores repetidos siempre que no sean nulos.", VF, "Falso",
         "La clave primaria debe identificar cada fila de forma única: no admite repetidos ni nulos.",
         "02:20", "RA4", "recordar", -0.5, 1.0),
        ("opcion_multiple", "¿Cuál es la función de una clave foránea?",
         ["Referenciar la clave primaria de otra tabla para relacionarlas", "Ordenar las filas de la tabla",
          "Cifrar los datos sensibles", "Evitar que existan índices"],
         "Referenciar la clave primaria de otra tabla para relacionarlas",
         "La clave foránea es el mecanismo que vincula una tabla con otra.",
         "03:10", "RA4", "comprender", -0.2, 1.0),
        ("opcion_multiple", "En Pedidos(id_pedido, id_cliente, fecha), ¿qué debes definir para que no existan pedidos de clientes inexistentes?",
         ["id_cliente como clave foránea hacia Clientes", "id_pedido como clave foránea hacia Clientes",
          "fecha como clave primaria", "Eliminar la clave primaria de Pedidos"],
         "id_cliente como clave foránea hacia Clientes",
         "La integridad referencial se impone con una clave foránea de id_cliente hacia la clave primaria de Clientes.",
         "04:00", "RA4", "aplicar", 0.3, 1.0),
        ("opcion_multiple", "¿Qué consulta devuelve el nombre de los estudiantes con nota mayor a 4,0 en Notas(estudiante, nombre, nota)?",
         ["SELECT nombre FROM Notas WHERE nota > 4.0;", "SELECT nota FROM Notas WHERE nombre > 4.0;",
          "SELECT * WHERE Notas.nota > 4.0;", "FROM Notas SELECT nombre IF nota > 4.0;"],
         "SELECT nombre FROM Notas WHERE nota > 4.0;",
         "El orden es SELECT columnas FROM tabla WHERE condición.",
         "04:50", "RA4", "aplicar", 0.5, 1.0),
        ("opcion_multiple", "Quieres listar TODOS los clientes, incluso los que nunca hicieron un pedido. ¿Qué combinación usas y por qué?",
         ["LEFT JOIN desde Clientes, porque conserva todas las filas de la tabla izquierda",
          "INNER JOIN, porque devuelve todas las filas de ambas tablas",
          "INNER JOIN, porque ignora las filas sin coincidencia y eso es lo que se quiere",
          "DELETE JOIN, porque elimina los clientes sin pedidos"],
         "LEFT JOIN desde Clientes, porque conserva todas las filas de la tabla izquierda",
         "INNER JOIN descarta los clientes sin pedidos; LEFT JOIN los conserva con valores nulos en las columnas de Pedidos.",
         "05:40", "RA2", "analizar", 1.0, 1.2),
        ("abierta", "Explica con tus palabras qué es la integridad referencial y por qué es importante en una base de datos relacional.", [],
         "La integridad referencial es la regla que garantiza que toda clave foránea apunte a una fila existente de la tabla referenciada (o sea nula). "
         "Es importante porque evita registros huérfanos, como pedidos de un cliente que no existe, y mantiene la consistencia entre tablas.",
         "Sin integridad referencial aparecerían datos huérfanos y resultados inconsistentes en las consultas.",
         "04:00", "RA4", "evaluar", 0.0, 1.0),
    ],
    "abierta": {
        "buena": ("Es una regla que asegura que una clave foránea siempre apunte a un registro que existe en la otra tabla. Sirve para que no queden datos huérfanos, por ejemplo un pedido de un cliente que ya fue borrado, y así la información se mantiene consistente.",
                  94, "Muy bien: explicas correctamente la regla y das un ejemplo claro de registros huérfanos.", ""),
        "media": ("Es que las tablas estén conectadas por las claves para que los datos se relacionen bien.",
                  58, "Identificas bien que la integridad referencial tiene que ver con las claves que conectan las tablas. Falta precisar que la clave foránea debe apuntar a una fila existente.",
                  "Que la clave foránea debe referenciar un registro existente y que así se evitan registros huérfanos."),
        "pobre": ("Es cuando la base de datos tiene muchas tablas y se hace copia de seguridad.",
                  12, "Mencionas tablas, pero la integridad referencial no se trata de copias de seguridad. Repasa el concepto de clave foránea.",
                  "La regla de que toda clave foránea apunte a una fila existente y el problema de los registros huérfanos."),
    },
}

# ---------------------------------------------------------------- 2. Normalización
Q2 = {
    "clave": "normalizacion",
    "titulo": "Normalización de bases de datos: 1FN, 2FN y 3FN",
    "resumen": (
        "La normalización organiza las tablas para reducir la redundancia y evitar anomalías de inserción, actualización y "
        "borrado. La 1FN exige atributos atómicos; la 2FN, que cada atributo no clave dependa de la clave completa; y la 3FN, "
        "que no existan dependencias transitivas. A veces se desnormaliza a propósito para mejorar el rendimiento."
    ),
    "ideas_clave": [
        "Normalizar reduce la redundancia y evita anomalías de inserción, actualización y borrado.",
        "1FN: atributos atómicos, sin grupos repetidos.",
        "2FN: sin dependencias parciales de la clave primaria compuesta.",
        "3FN: sin dependencias transitivas entre atributos no clave.",
        "Desnormalizar puede ser una decisión válida para mejorar el rendimiento.",
    ],
    "video": {"youtube_id": "MdYvCMbQji4", "titulo": "Normalización (1FN, 2FN, 3FN) - BASE DE DATOS"},
    "transcripcion": [
        (0, "La normalización es el proceso de organizar las tablas de una base de datos para reducir la redundancia y evitar anomalías de inserción, actualización y borrado."),
        (40, "Una tabla está en primera forma normal, 1FN, cuando todos sus atributos son atómicos: no hay grupos repetidos ni celdas con varios valores."),
        (90, "Por ejemplo, si un estudiante tiene una columna teléfonos con tres números separados por comas, hay que separarlos en filas o pasarlos a otra tabla."),
        (130, "La segunda forma normal, 2FN, exige estar en 1FN y que todo atributo no clave dependa de la clave primaria completa, no solo de una parte. Esto solo aplica cuando la clave es compuesta."),
        (180, "La tercera forma normal, 3FN, exige estar en 2FN y que no existan dependencias transitivas: un atributo no clave no puede depender de otro atributo no clave."),
        (220, "Por ejemplo, si guardamos ciudad y departamento en la tabla de empleados, el departamento depende de la ciudad; se separa en otra tabla."),
        (250, "Normalizar reduce la redundancia, pero un exceso de tablas exige más JOIN; a veces se desnormaliza a propósito para mejorar el rendimiento de las consultas."),
    ],
    "preguntas": [
        ("opcion_multiple", "¿Cuál es el principal objetivo de la normalización?",
         ["Reducir la redundancia y evitar anomalías de actualización", "Aumentar los datos duplicados para consultar más rápido",
          "Cifrar la información", "Eliminar las claves primarias"],
         "Reducir la redundancia y evitar anomalías de actualización",
         "Normalizar organiza los datos para que cada hecho se guarde una sola vez.",
         "00:00", "RA4", "recordar", -1.3, 1.0),
        ("opcion_multiple", "Una tabla está en primera forma normal (1FN) cuando…",
         ["todos sus atributos son atómicos, sin grupos repetidos", "todos los atributos dependen de la clave completa",
          "no tiene dependencias transitivas", "tiene al menos tres claves foráneas"],
         "todos sus atributos son atómicos, sin grupos repetidos",
         "La 1FN exige valores atómicos; la dependencia de la clave completa es la 2FN y la ausencia de transitivas, la 3FN.",
         "00:40", "RA4", "comprender", -0.9, 1.0),
        ("verdadero_falso", "La 2FN solo es relevante cuando la clave primaria es compuesta.", VF, "Verdadero",
         "Con clave simple no puede haber dependencia parcial, así que una tabla en 1FN ya cumple la 2FN.",
         "02:10", "RA4", "comprender", 0.0, 1.0),
        ("opcion_multiple", "Estudiante(id, nombre, telefonos) guarda «3001234567, 3109876543» en telefonos. ¿Qué forma normal incumple?",
         ["Primera forma normal (atomicidad)", "Segunda forma normal", "Tercera forma normal", "Ninguna, está normalizada"],
         "Primera forma normal (atomicidad)",
         "Varios valores en una misma celda violan la atomicidad exigida por la 1FN.",
         "01:30", "RA4", "aplicar", -0.3, 1.0),
        ("opcion_multiple", "En Matricula(id_estudiante, id_curso, nombre_curso, nota) la clave es (id_estudiante, id_curso) y nombre_curso depende solo de id_curso. ¿Qué violación hay?",
         ["Dependencia parcial: viola la 2FN", "Dependencia transitiva: viola la 3FN", "Grupo repetido: viola la 1FN", "No hay violación"],
         "Dependencia parcial: viola la 2FN",
         "Un atributo no clave que depende de solo una parte de la clave compuesta es una dependencia parcial.",
         "02:10", "RA4", "aplicar", 0.4, 1.0),
        ("opcion_multiple", "En Empleado(id, nombre, ciudad, departamento), departamento depende de ciudad. ¿Cómo se llega a 3FN?",
         ["Crear Ciudad(ciudad, departamento) y dejar solo ciudad en Empleado", "Duplicar la columna departamento",
          "Eliminar la columna nombre", "Convertir id en clave compuesta con departamento"],
         "Crear Ciudad(ciudad, departamento) y dejar solo ciudad en Empleado",
         "Se elimina la dependencia transitiva id → ciudad → departamento separando esos atributos en otra tabla.",
         "03:40", "RA2", "analizar", 0.7, 1.1),
        ("verdadero_falso", "Desnormalizar nunca es recomendable porque siempre empeora el rendimiento.", VF, "Falso",
         "A veces se desnormaliza a propósito para evitar JOIN costosos y acelerar consultas.",
         "04:10", "RA2", "evaluar", 0.4, -0.7),
        ("abierta", "Explica qué es una dependencia transitiva y da un ejemplo.", [],
         "Es cuando un atributo no clave depende de otro atributo no clave y no directamente de la clave primaria (A → B y B → C implica A → C). "
         "Ejemplo: en Empleado(id, ciudad, departamento), departamento depende de ciudad, que a su vez depende de id; debe separarse en otra tabla para cumplir la 3FN.",
         "Las dependencias transitivas generan redundancia y anomalías de actualización.",
         "03:00", "RA4", "comprender", 0.2, 1.0),
    ],
    "abierta": {
        "buena": ("Es cuando una columna que no es la clave depende de otra columna que tampoco es la clave. Por ejemplo, en una tabla de empleados el departamento depende de la ciudad, y la ciudad depende del id; por eso hay que pasar ciudad y departamento a otra tabla para quedar en 3FN.",
                  96, "Excelente: defines bien la dependencia transitiva y tu ejemplo con ciudad y departamento es correcto.", ""),
        "media": ("Es cuando un dato depende de otro dato que no es la clave principal.",
                  62, "Vas por buen camino: captas que un atributo depende de otro que no es la clave. Faltó un ejemplo concreto y mencionar la 3FN.",
                  "Un ejemplo (p. ej. departamento que depende de ciudad) y que se corrige separando en otra tabla."),
        "pobre": ("Es cuando una tabla se pasa de una base de datos a otra.",
                  8, "No es lo que se pregunta: la dependencia transitiva se refiere a cómo dependen los atributos entre sí.",
                  "Que un atributo no clave depende de otro atributo no clave (A → B → C) y un ejemplo."),
    },
}

# ---------------------------------------------------------------- 3. Ordenamiento
Q3 = {
    "clave": "ordenamiento",
    "titulo": "Algoritmos de ordenamiento: burbuja, inserción y Quick Sort",
    "resumen": (
        "Un algoritmo de ordenamiento reorganiza una lista según un criterio. Burbuja, selección e inserción son sencillos pero "
        "O(n²) en general; la inserción es O(n) en el mejor caso. Quick Sort y Merge Sort usan divide y vencerás y logran "
        "O(n log n). La estabilidad indica si se conserva el orden relativo de los elementos iguales."
    ),
    "ideas_clave": [
        "Burbuja compara pares adyacentes y los intercambia; es O(n²).",
        "La inserción es eficiente en listas casi ordenadas (O(n) en el mejor caso).",
        "Quick Sort usa un pivote y divide y vencerás; promedio O(n log n).",
        "Merge Sort garantiza O(n log n) pero necesita memoria adicional.",
        "Un algoritmo estable conserva el orden relativo de los elementos iguales.",
    ],
    "video": {"youtube_id": "GBdjJajfR3k", "titulo": "Algoritmos de ordenamiento - Método Burbuja y Quick Sort en Java"},
    "transcripcion": [
        (0, "Un algoritmo de ordenamiento reorganiza los elementos de una lista según un criterio, por ejemplo de menor a mayor."),
        (50, "El método burbuja compara pares de elementos adyacentes y los intercambia si están en el orden incorrecto; repite el recorrido hasta que no haya más intercambios."),
        (120, "La complejidad del burbuja es O(n²) en el peor caso y en el caso promedio, por lo que es poco eficiente con listas grandes; su ventaja es que es sencillo."),
        (180, "El ordenamiento por selección busca el mínimo de la parte no ordenada y lo coloca en la siguiente posición; también es O(n²)."),
        (230, "El ordenamiento por inserción toma un elemento y lo inserta en su lugar dentro de la parte ya ordenada; es eficiente en listas casi ordenadas, con O(n) en el mejor caso."),
        (290, "Quick Sort usa la estrategia de divide y vencerás: elige un pivote, separa los elementos menores y mayores y ordena recursivamente cada parte. Su caso promedio es O(n log n)."),
        (360, "Merge Sort también es divide y vencerás, garantiza O(n log n) en todos los casos pero necesita memoria adicional."),
        (420, "Un algoritmo es estable si conserva el orden relativo de los elementos iguales; burbuja e inserción son estables, Quick Sort normalmente no."),
    ],
    "preguntas": [
        ("opcion_multiple", "¿Qué hace el método de ordenamiento burbuja?",
         ["Compara pares adyacentes y los intercambia si están desordenados", "Elige un pivote y divide la lista",
          "Divide la lista en mitades y las mezcla", "Busca el mínimo y lo coloca al inicio"],
         "Compara pares adyacentes y los intercambia si están desordenados",
         "Quick Sort usa pivote, Merge Sort mezcla mitades y selección busca el mínimo.",
         "00:50", "RA1", "recordar", -1.2, 1.0),
        ("verdadero_falso", "La complejidad del ordenamiento burbuja en el caso promedio es O(n²).", VF, "Verdadero",
         "Burbuja recorre la lista repetidamente: en el caso promedio y en el peor realiza del orden de n² comparaciones.",
         "02:00", "RA1", "recordar", -0.8, 1.0),
        ("opcion_multiple", "¿Por qué el ordenamiento por inserción es eficiente en listas casi ordenadas?",
         ["Porque casi no desplaza elementos y en el mejor caso hace O(n) comparaciones", "Porque usa un pivote",
          "Porque requiere memoria adicional", "Porque siempre es O(log n)"],
         "Porque casi no desplaza elementos y en el mejor caso hace O(n) comparaciones",
         "Si cada elemento ya está casi en su lugar, la inserción apenas hace desplazamientos.",
         "03:50", "RA3", "comprender", -0.1, 1.0),
        ("opcion_multiple", "¿Qué estrategia usa Quick Sort?",
         ["Divide y vencerás con un pivote", "Fuerza bruta", "Programación dinámica", "Búsqueda binaria"],
         "Divide y vencerás con un pivote",
         "Quick Sort particiona alrededor de un pivote y ordena recursivamente cada parte.",
         "04:50", "RA3", "comprender", -0.4, 1.0),
        ("opcion_multiple", "Aplicando UNA pasada del burbuja a [5, 1, 4, 2] de menor a mayor, ¿cómo queda la lista?",
         ["[1, 4, 2, 5]", "[1, 2, 4, 5]", "[5, 1, 2, 4]", "[1, 5, 4, 2]"], "[1, 4, 2, 5]",
         "5↔1 → [1,5,4,2]; 5↔4 → [1,4,5,2]; 5↔2 → [1,4,2,5]. El mayor «burbujea» al final en la primera pasada.",
         "00:50", "RA1", "aplicar", 0.5, 1.0),
        ("opcion_multiple", "Debes ordenar un millón de registros y tienes memoria suficiente. ¿Qué algoritmo conviene y por qué?",
         ["Merge Sort o Quick Sort, por su complejidad O(n log n)", "Burbuja, por ser el más sencillo",
          "Selección, porque siempre es estable", "Inserción, porque es O(n) siempre"],
         "Merge Sort o Quick Sort, por su complejidad O(n log n)",
         "Con n grande, O(n log n) supera ampliamente a O(n²).",
         "06:00", "RA3", "analizar", 0.8, 1.0),
        ("opcion_multiple", "Ordenas por apellido y luego por nombre conservando el orden previo de los iguales. ¿Qué propiedad debe tener el algoritmo?",
         ["Estabilidad", "Recursividad", "Uso de un pivote", "Complejidad O(1)"], "Estabilidad",
         "Un algoritmo estable conserva el orden relativo de los elementos con la misma clave.",
         "07:00", "RA3", "analizar", 1.0, 1.1),
        ("abierta", "Compara el ordenamiento burbuja con Quick Sort: ¿cuál es más eficiente para listas grandes y por qué?", [],
         "Quick Sort es más eficiente: usa divide y vencerás con un pivote y su complejidad promedio es O(n log n), mientras que burbuja compara pares adyacentes "
         "repetidamente con O(n²). Con listas grandes la diferencia es enorme; burbuja solo se justifica por su simplicidad y para listas pequeñas.",
         "La elección depende del tamaño de la lista y de la complejidad del algoritmo.",
         "04:50", "RA1", "evaluar", 0.2, 1.0),
    ],
    "abierta": {
        "buena": ("Quick Sort es mucho más eficiente en listas grandes porque divide la lista con un pivote y ordena cada parte (divide y vencerás), con complejidad promedio O(n log n). Burbuja va comparando de dos en dos muchas veces y es O(n²), así que solo sirve para listas chicas o por su simplicidad.",
                  95, "Excelente comparación: cubres la complejidad de ambos y la estrategia de Quick Sort.", ""),
        "media": ("Quick Sort es más rápido que burbuja porque usa un pivote, y burbuja es más lento.",
                  64, "Bien: eliges correctamente a Quick Sort y mencionas el pivote. Te faltó indicar las complejidades (O(n log n) frente a O(n²)).",
                  "Las complejidades de cada algoritmo y por qué importan en listas grandes."),
        "pobre": ("Los dos son iguales, solo cambia el nombre.",
                  10, "Los dos algoritmos son distintos: tienen estrategias y complejidades diferentes. Repasa el video desde el minuto 04:50.",
                  "Que Quick Sort es divide y vencerás con O(n log n) promedio y burbuja es O(n²)."),
    },
}

# ---------------------------------------------------------------- 4. TCP/IP
Q4 = {
    "clave": "tcpip",
    "titulo": "Redes de computadores: el modelo TCP/IP",
    "resumen": (
        "El modelo TCP/IP organiza la comunicación en cuatro capas: acceso a red, internet, transporte y aplicación. IP "
        "direcciona y enruta paquetes (IPv4 de 32 bits, IPv6 de 128), TCP ofrece comunicación confiable y UDP es más rápido "
        "sin garantizar la entrega, y en la capa de aplicación trabajan HTTP, SMTP, DNS y FTP."
    ),
    "ideas_clave": [
        "TCP/IP tiene cuatro capas: acceso a red, internet, transporte y aplicación.",
        "IP direcciona y enruta paquetes entre redes; IPv4 usa 32 bits e IPv6, 128.",
        "TCP es confiable y orientado a la conexión; UDP es más rápido pero no garantiza la entrega.",
        "DNS traduce nombres de dominio a direcciones IP.",
        "Abrir una página web combina DNS, TCP y HTTP.",
    ],
    "video": {"youtube_id": "1pB2kan_AFk", "titulo": "Un resumen completo del modelo TCP/IP (todas sus capas en menos de 7 minutos)"},
    "transcripcion": [
        (0, "El modelo TCP/IP organiza la comunicación en red en cuatro capas: acceso a red, internet, transporte y aplicación."),
        (50, "La capa de acceso a red se encarga de la transmisión física de los datos en el medio, como Ethernet o Wi-Fi, usando direcciones MAC."),
        (110, "La capa de internet usa el protocolo IP para direccionar los paquetes y enrutarlos entre redes diferentes; aquí trabajan los routers. Para salir a otra red, el equipo necesita una puerta de enlace (gateway) configurada, que es el router."),
        (170, "IPv4 usa direcciones de 32 bits, por ejemplo 192.168.1.10, mientras que IPv6 usa 128 bits para resolver el agotamiento de direcciones."),
        (220, "En la capa de transporte, TCP ofrece una comunicación confiable y orientada a la conexión, con control de errores y reenvío; UDP es más rápido pero no garantiza la entrega, y por eso se usa en videollamadas y juegos en línea."),
        (290, "La capa de aplicación contiene los protocolos que usan los programas: HTTP y HTTPS para la web, SMTP para el correo, DNS para traducir nombres de dominio a direcciones IP y FTP para transferir archivos. Si el DNS falla, no se resuelven los nombres aunque haya conexión."),
        (360, "Por ejemplo, al abrir una página web, DNS resuelve el nombre, TCP establece la conexión con el saludo de tres vías y HTTP solicita la página."),
    ],
    "preguntas": [
        ("opcion_multiple", "¿Cuántas capas tiene el modelo TCP/IP?",
         ["Cuatro", "Siete", "Tres", "Cinco"], "Cuatro",
         "TCP/IP tiene cuatro capas; el modelo OSI, de referencia, tiene siete.",
         "00:00", "RA6", "recordar", -1.3, 1.0),
        ("opcion_multiple", "¿Qué protocolo traduce nombres de dominio a direcciones IP?",
         ["DNS", "SMTP", "FTP", "UDP"], "DNS",
         "DNS resuelve nombres como ejemplo.com a su dirección IP.",
         "04:50", "RA6", "recordar", -1.0, 1.0),
        ("verdadero_falso", "UDP garantiza la entrega de los datos con control de errores y reenvío.", VF, "Falso",
         "Eso lo hace TCP; UDP es más rápido pero no garantiza la entrega.",
         "03:40", "RA6", "comprender", -0.4, 1.0),
        ("opcion_multiple", "¿En qué capa trabajan los routers para enrutar paquetes entre redes?",
         ["Internet", "Aplicación", "Transporte", "Acceso a red"], "Internet",
         "La capa de internet usa IP para direccionar y enrutar los paquetes entre redes.",
         "01:50", "RA6", "comprender", -0.2, 1.0),
        ("opcion_multiple", "Una videollamada prioriza la velocidad sobre la fiabilidad perfecta. ¿Qué protocolo de transporte conviene?",
         ["UDP", "TCP", "SMTP", "DNS"], "UDP",
         "UDP evita el costo de las confirmaciones y reenvíos de TCP; tolera pérdidas leves.",
         "03:40", "RA6", "aplicar", 0.4, 1.0),
        ("opcion_multiple", "Al abrir una página web, ¿en qué orden ocurren los pasos principales?",
         ["DNS resuelve el nombre, TCP establece la conexión y HTTP solicita la página",
          "HTTP solicita la página, DNS resuelve el nombre y luego TCP conecta",
          "TCP conecta, HTTP solicita y luego DNS resuelve", "SMTP envía la página y DNS la recibe"],
         "DNS resuelve el nombre, TCP establece la conexión y HTTP solicita la página",
         "Primero se necesita la IP (DNS), luego la conexión (TCP) y por último la petición (HTTP).",
         "06:00", "RA6", "aplicar", 0.3, 1.0),
        ("opcion_multiple", "Un equipo tiene la IP 192.168.1.10 pero no sale a internet, aunque otros equipos sí. ¿Qué verificarías primero?",
         ["Que la puerta de enlace (gateway) y el DNS estén bien configurados", "Que el equipo use direcciones IPv6 de 128 bits",
          "Que HTTP sea más lento que HTTPS", "Que la capa de aplicación tenga routers"],
         "Que la puerta de enlace (gateway) y el DNS estén bien configurados",
         "Sin gateway no se sale de la red local y sin DNS no se resuelven los nombres.",
         "02:10", "RA6", "analizar", 1.0, 1.2),
        ("abierta", "Explica la diferencia entre TCP y UDP y menciona un caso de uso de cada uno.", [],
         "TCP es confiable y orientado a la conexión: controla errores y reenvía lo perdido, por eso se usa en web, correo o transferencia de archivos. "
         "UDP es más rápido pero no garantiza la entrega, por eso se usa en videollamadas, streaming o juegos en línea.",
         "La elección depende de si importa más la fiabilidad o la velocidad.",
         "03:40", "RA6", "comprender", 0.1, 1.0),
    ],
    "abierta": {
        "buena": ("TCP es confiable: establece una conexión, revisa errores y reenvía lo que se pierde, por eso se usa para páginas web o correos. UDP no garantiza que lleguen los datos pero es más rápido, y se usa en videollamadas o juegos online.",
                  93, "Muy buena respuesta: diferencias bien la fiabilidad de TCP y la velocidad de UDP y das un caso de uso de cada uno.", ""),
        "media": ("TCP es más seguro y UDP es más rápido.",
                  55, "Correcto: TCP es el confiable y UDP el rápido. Faltó explicar por qué (control de errores, reenvío) y dar casos de uso.",
                  "Un ejemplo de uso de cada protocolo y el motivo de la diferencia."),
        "pobre": ("TCP es una marca de computadores y UDP un tipo de cable.",
                  5, "Ambos son protocolos de la capa de transporte, no marcas ni cables. Repasa el video desde el minuto 03:40.",
                  "Que TCP es confiable y orientado a la conexión y UDP es rápido sin garantía de entrega, con ejemplos."),
    },
}

QUIZZES = {q["clave"]: q for q in (Q1, Q2, Q3, Q4)}

ESTUDIANTES = [
    # (nombre, perfil, grupo)  grupo: 0 = Bases de Datos, 1 = Estructuras de Datos, 2 = Redes
    ("Valentina Gómez Ruiz", "bueno", 0), ("Santiago Rodríguez Peña", "bueno", 0), ("Mariana López Cardona", "bueno", 0),
    ("Sebastián Martínez Torres", "medio", 0), ("Camila Hernández Ríos", "medio", 0), ("Juan David Castro Ospina", "medio", 0),
    ("Daniela Vargas Muñoz", "inactivo", 0), ("Andrés Felipe Ramírez Gil", "bajo", 0), ("Laura Sofía Moreno Parra", "caida", 0),
    ("Mateo Jiménez Salazar", "bueno", 1), ("Isabella Pérez Duque", "bueno", 1),
    ("Nicolás Torres Giraldo", "medio", 1), ("Sara Valentina Díaz Mesa", "medio", 1), ("Samuel Ortiz Cano", "medio", 1),
    ("Luisa Fernanda Rojas Vega", "bajo", 1), ("Daniel Mejía Restrepo", "inactivo", 1), ("María José Acosta León", "caida", 1),
    ("Julián Esteban Cruz Franco", "bueno", 2), ("Paula Andrea Herrera Soto", "bueno", 2),
    ("Felipe Arango Londoño", "medio", 2), ("Natalia Suárez Bedoya", "medio", 2), ("Esteban Quintero Mora", "medio", 2),
    ("Karen Johana Patiño Lara", "bajo", 2), ("Camilo Andrés Zapata Ríos", "vencidos", 2),
]

BANCO_ETIQUETAS = {"relacional": ["sql", "claves"], "normalizacion": ["formas normales"], "ordenamiento": ["complejidad"], "tcpip": ["protocolos"]}

COMENTARIOS_SUS = [
    "Muy fácil de usar, me gustó poder repasar con el video.",
    "Las preguntas con el minuto del video ayudan mucho a estudiar.",
    "La clase en vivo con el PIN es muy dinámica.",
    "A veces tarda en cargar cuando hay muchos estudiantes.",
    "Me gustaría ver más cuestionarios de otras materias.",
    "Sencilla, aunque al principio no sabía dónde unirme al grupo.",
    "El tutor del video me resolvió dudas antes del parcial.",
]
