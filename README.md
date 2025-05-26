# LoveLink
La aplicación que recomienda posibles parejas en base a un grafo social que contiene datos como amistades, exparejas e interacciones Utilizando algoritmos de grafos, como "Friend-of-a-Friend", se buscarán conexiones no evidentes pero prometedoras El objetivo es generar recomendaciones de manera personalizada manteniendo la privacidad de los usuarios.




# 🧠 Modelado del Grafo - LoveLink

## 👤 Nodos: `Person`

Cada persona en el sistema se representa como un nodo `:Person` con los siguientes atributos:

| Atributo    | Tipo      | Descripción                                |
|-------------|-----------|--------------------------------------------|
| `name`      | `string`  | Nombre de la persona                       |
| `age`       | `integer` | Edad                                       |
| `gender`    | `string`  | Género (ej. `"M"`, `"F"`, `"NB"`...)       |
| `interests` | `list`    | Lista de intereses (ej. `"cine"`, `"arte"`) |

## 🔗 Relaciones en el Grafo

El sistema modela distintos tipos de relaciones entre nodos `Person`. Cada tipo tiene una finalidad distinta dentro del algoritmo de recomendación.

---

### 👫 `[:FRIEND]`

- **Descripción:** Representa una amistad o conexión social entre dos personas.
- **Direccionalidad:** Dirigida (opcionalmente se puede duplicar si se desea simular bidireccionalidad).
- **Motivación:**
  - Permite encontrar conexiones indirectas (“amigos de amigos”).
  - Ayuda a evitar sugerencias demasiado lejanas o aleatorias.


### ❤️ [:DATED]

- **Descripción:** Indica que dos personas mantuvieron una relación romántica en el pasado.
- **Direccionalidad:** Dirigida (puede duplicarse si se desea simular reciprocidad).
- **Motivación:**
  - Evitar recomendar ex-parejas.
  - Analizar compatibilidades pasadas para detectar patrones de elección.



### 💬 [:INTERACTED_WITH]

- **Descripción:** Representa una interacción puntual entre dos personas (ej. un “like” o un mensaje).
- **Direccionalidad:** Dirigida desde quien inicia la interacción hacia la otra persona.
- **Motivación:**
  - Refleja interés reciente o histórico.
  - Útil para calcular niveles de engagement o señales mutuas de atracción.
