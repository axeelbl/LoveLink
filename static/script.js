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
      card.innerHTML = `
        <img src="${person.profile_picture || "/static/default.jpg"}" alt="${person.name}" class="profile-img"><br>
        <strong>${person.name}</strong><br>
        Edad: ${person.age}<br>
        Género: ${person.gender}<br>
        Intereses: ${person.interests.join(", ")}
      `;
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
        const profileImage = person.profile_picture || "/static/default.jpg";
        const interests = Array.isArray(person.interests) ? person.interests.join(", ") : "No especificados";

        card.innerHTML = `
          <img src="${profileImage}" alt="Foto de ${person.name}" class="profile-img"
            onerror="this.onerror=null; this.src='/static/default.jpg';" />
          <h3>${person.name}</h3>
          <p><strong>Edad:</strong> ${person.age}</p>
          <p><strong>Género:</strong> ${person.gender}</p>
          <p><strong>Intereses:</strong> ${interests}</p>
          <p><strong>Motivo:</strong> ${person.reason}</p>
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
    showToast('Por favor, introduce el nombre de la persona.');
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


//Funciones para enviar relaciones
async function getCurrentUserName() {
  const res = await fetch("/me", { credentials: "include" });
  if (!res.ok) throw new Error("No logueado");
  const data = await res.json();
  return data.name; 
}

async function sendRelationship(toName, type) {
  try {
    const me = await getCurrentUserName();
    const res = await fetch("/relationship/", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from_person: me,
        to_person: toName,
        type: type
      })
    });

    const data = await res.json();
    showToast(data.message);

    // Vuelve a buscar para actualizar la tarjeta del usuario
    await searchUsers();
  } catch (err) {
    showToast("Error al crear relación.");
  }
}

async function sendInterest(toName) {
  try {
    const me = await getCurrentUserName();
    const res = await fetch("/interest/", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from_person: me,
        to_person: toName
      })
    });

    const data = await res.json();
    showToast(data.message);
  } catch (err) {
    showToast("Error al expresar interés.");
  }
}

async function sendInteraction(toName, interactionType = "mensaje") {
  try {
    const me = await getCurrentUserName();
    const res = await fetch("/relationship/", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from_person: me,
        to_person: toName,
        type: "INTERACTED_WITH",
        interaction_type: interactionType,
        timestamp: new Date().toISOString()
      })
    });

    const data = await res.json();
    showToast(data.message);
  } catch (err) {
    showToast("Error al registrar interacción.");
  }
}


// Función para buscar users
async function searchUsers() {
  const query = document.getElementById("search-query").value.trim();
  if (!query) {
    showToast("Introduce un nombre para buscar.");
    return;
  }

  const res = await fetch(`/search_users?query=${encodeURIComponent(query)}`, {
    credentials: "include"
  });

  const data = await res.json();
  const list = document.getElementById("search-users-results");
  list.innerHTML = "";

  if (data.length === 0) {
    list.innerHTML = "<p style='color:white;'>No se encontraron usuarios.</p>";
    return;
  }

  data.forEach(user => {
    const card = document.createElement("div");
    card.className = "card";

    let relationButtons = '';

    if (user.relationship === "FRIEND") {
      relationButtons += `<button style="background-color:red;" onclick="cancelRelationship('${user.name}', 'FRIEND')">Cancelar amistad</button>`;
    } else {
      relationButtons += `<button onclick="sendRelationship('${user.name}', 'FRIEND')">Amistad</button>`;
    }

    if (user.relationship === "DATED") {
      relationButtons += `<button style="background-color:red;" onclick="cancelRelationship('${user.name}', 'DATED')">Cancelar pareja</button>`;
    } else {
      relationButtons += `<button onclick="sendRelationship('${user.name}', 'DATED')">Pareja</button>`;
    }

    card.innerHTML = `
      <img src="${user.profile_picture}" alt="Foto de ${user.name}" class="profile-img">
      <h3>${user.name}</h3>
      <p>${user.email}</p>
      ${relationButtons}
      <button onclick="sendInterest('${user.name}')">Me interesa</button>
      <button onclick="sendInteraction('${user.name}', 'mensaje')">Interacción</button>
    `;

    list.appendChild(card);
  });

  await loadMyRecommendations();

}

// Función para mostar Toast
function showToast(message) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);

  // Desaparece y elimina después de 3 segundos
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => container.removeChild(toast), 300);
  }, 3000);
}

// Función para cancelar relaciones
async function cancelRelationship(toName, type) {
  try {
    const me = await getCurrentUserName();
    const res = await fetch("/relationship/", {
      method: "DELETE",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from_person: me,
        to_person: toName,
        type: type
      })
    });

    const data = await res.json();
    showToast(data.message);

    // Vuelve a buscar para actualizar la interfaz
    await searchUsers();
  } catch (err) {
    showToast("Error al cancelar relación.");
  }
}
// Función para ir a mis relaciones
function goToMyRelationships() {
  window.location.href = "mis-relaciones";
}