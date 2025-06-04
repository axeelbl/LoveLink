//script.js

// Función para cargar recomendaciones de los usuarios que tú introduzcas
async function getRecommendations() {
  const name = document.getElementById("rec-name").value;
  const res = await fetch(`/recommendations/${name}`, {
    credentials: "include"
  });
  const data = await res.json();

  const list = document.getElementById("search-recommendation-list");
  list.innerHTML = "";

  data.recommendations.forEach(person => {
    const card = document.createElement("div");
    card.className = "card";

    if (typeof person === "string") {
      card.textContent = person;
    } else {
      card.innerHTML =
        `<strong>${person.name}</strong><br>
        Edad: ${person.age}<br>
        Género: ${person.gender}<br>
        Intereses: ${person.interests.join(", ")}`;
    }

    list.appendChild(card);
  });
}


// Función para cargar el camino
async function getPath() {
  const from = document.getElementById("from-name").value;
  const to = document.getElementById("to-name").value;
  const res = await fetch(`/path-to/${from}/${to}`, {
    credentials: "include"
  });
  const data = await res.json();

  const list = document.getElementById("path-results");
  list.innerHTML = "";

  data.path.forEach((name, i) => {
    const node = document.createElement("div");
    node.className = "path-node";
    node.textContent = name;
    list.appendChild(node);

    if (i < data.types.length) {
      const arrow = document.createElement("div");
      arrow.className = "path-arrow";
      arrow.innerHTML = `→ <em>${data.types[i]}</em>`;
      list.appendChild(arrow);
    }
  });
}

// Función para desloguearse
function logout() {
  fetch("/logout", {
    method: "GET",
    credentials: "include"
  }).then(() => {
    window.location.href = "/login-page";
  });
}

// Función para cargar recomendaciones del user logeado
document.addEventListener("DOMContentLoaded", () => {
  loadMyRecommendations();
});

async function loadMyRecommendations() {
  try {
    const response = await fetch("/user-logged-recommendations", {
      method: "GET",
      credentials: "include"
    });

    if (!response.ok) {
      console.error("Error cargando recomendaciones", await response.text());
      return;
    }

    const data = await response.json();
    const list = document.getElementById("my-recommendation-list");
    list.innerHTML = "";

    if (!data.recommendations || data.recommendations.length === 0) {
      list.innerHTML = "<p style='color: white;'>No tienes recomendaciones aún.<br>Agrega a amigos para obtener recomendaciones.</p>";
      return;
    }

    data.recommendations.forEach(person => {
      const card = document.createElement("div");
      card.className = "card";

      if (typeof person === "string") {
        card.textContent = person;
      } else {
        card.innerHTML = `
          <strong>${person.name}</strong><br>
          Edad: ${person.age}<br>
          Género: ${person.gender}<br>
          Intereses: ${person.interests.join(", ")}<br>
          Motivo: ${person.reason}
        `;
      }

      list.appendChild(card);
    });

  } catch (error) {
    console.error("Error en la petición a /user-logged-recommendations:", error);
  }
}


// Función para leer cookies
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

// Función para que el user loggeado pueda buscar el camino.
function renderPath(data) {
  const list = document.getElementById("path-results-logged");
  list.innerHTML = "";

  // Comprobar que data.path existe y tiene contenido
  if (!data.path || data.path.length === 0) {
    list.textContent = "Usuario no encontrado.";
    return;
  }

  data.path.forEach((name, i) => {
    const node = document.createElement("div");
    node.className = "path-node";
    node.textContent = name;
    list.appendChild(node);

    if (i < data.types.length) {
      const arrow = document.createElement("div");
      arrow.className = "path-arrow";
      arrow.innerHTML = `→ <em>${data.types[i]}</em>`;
      list.appendChild(arrow);
    }
  });
}
async function getPathFromLoggedUser() {
  const to = document.getElementById('to-name-logged').value.trim();
  if (!to) {
    alert('Por favor, introduce el nombre de la persona.');
    return;
  }

  // Opcional: muestra mensaje mientras carga
  document.getElementById('path-results-logged').innerHTML = 'Cargando camino...';

  try {
    const res = await fetch(`/path-to-user/${encodeURIComponent(to)}`, {
      credentials: 'include'
    });

    if (!res.ok) {
      throw new Error(`Error en la petición: ${res.status}`);
    }

    const data = await res.json();

    // Aquí llama a la función que muestra el camino en pantalla
    renderPath(data, 'path-results-logged');

  } catch (error) {
    document.getElementById('path-results-logged').innerHTML = `Error: ${error.message}`;
  }
}


// Función para ir a tu perfil.
function goToProfile() {
  window.location.href = "/profile";
}