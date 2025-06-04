async function getCurrentUser() {
  const res = await fetch("/whoami", { credentials: "include" });
  if (!res.ok) throw new Error("No logueado");
  const data = await res.json();
  return data;  // ya tienes {name, email, age, gender, interests, profile_picture}
}

async function loadRelationships() {
  try {
    const currentUser = await getCurrentUser();  // Obtenemos todos los datos
    const name = currentUser.name;

    const res = await fetch(`/person/${name}/relationships`, { credentials: "include" });
    const relationships = await res.json();

    const container = document.getElementById("relationships-list");
    container.innerHTML = "";

    if (relationships.length === 0) {
      container.innerHTML = "<p>No tienes relaciones activas.</p>";
      return;
    }

    for (const rel of relationships) {
      // Datos del otro usuario (fetch)
      const userRes = await fetch(`/person/${rel.with}`, { credentials: "include" });
      const other = await userRes.json();

      // Formatear intereses (array a string, si está vacío)
      const intereses = (other.interests && other.interests.length > 0) 
                        ? other.interests.join(", ") 
                        : "No especificados";

      // Mostrar género con fallback
      const genero = other.gender || "No especificado";

      // Imagen con fallback
      const imgSrc = other.profile_picture || "/static/default.jpg";

      // Crear tarjeta con datos completos
      const card = document.createElement("div");
      card.className = "card";

      card.innerHTML = `
        <img src="${imgSrc}" alt="Foto de ${other.name}" onerror="this.src='/static/default.jpg'">
        <h3>${other.name}</h3>
        <p class="relation-type">${formateaTipo(rel.type)}</p>
        <p><strong>Género:</strong> ${genero}</p>
        <p><strong>Intereses:</strong> ${intereses}</p>
        <button class="delete-btn" onclick="deleteRelationship('${name}', '${other.name}', '${rel.type}')">❌ Cancelar relación</button>
      `;

      container.appendChild(card);
    }
  } catch (error) {
    console.error(error);
    alert("Error al cargar relaciones.");
  }
}


function formateaTipo(tipo) {
  switch (tipo) {
    case "FRIEND": return "Amistad";
    case "DATED": return "Pareja";
    case "INTERESTED_IN": return "Interés";
    case "INTERACTED_WITH": return "Interacción";
    default: return tipo;
  }
}

async function deleteRelationship(from, to, type) {
  try {
    const res = await fetch(`/relationship/delete`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ from_person: from, to_person: to, type: type })
    });

    const data = await res.json();
    alert(data.message || "Relación eliminada.");
    loadRelationships(); // Recargar lista
  } catch (err) {
    console.error(err);
    alert("Error al eliminar relación.");
  }
}

window.onload = loadRelationships;
