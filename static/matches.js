async function getCurrentUserName() {
  const res = await fetch("/me", { credentials: "include" });
  if (!res.ok) throw new Error("No logueado");
  const data = await res.json();
  return data.name;
}

function getProfileImage(profile_picture) {
  if (!profile_picture) return "/static/default.jpg";
  return profile_picture;
}

async function loadMatches() {
  try {
    const name = await getCurrentUserName();
    const res = await fetch(`/matches/${encodeURIComponent(name)}`, { credentials: "include" });
    if (!res.ok) throw new Error("No se pudo cargar los matches");
    const matches = await res.json();

    const container = document.getElementById("matches-list");
    container.innerHTML = "";

    if (matches.length === 0) {
      container.innerHTML = "<p>No tienes matches todavía.</p>";
      return;
    }

    for (const m of matches) {
      const interests = (m.interests && m.interests.length > 0) ? m.interests.join(", ") : "No especificados";
      const profileImage = getProfileImage(m.profile_picture);

      container.innerHTML += `
        <div class="card">
          <img src="${profileImage}" alt="Foto de ${m.name}" onerror="this.src='/static/default.jpg'"/>
          <h3>${m.name}, ${m.age || "Edad no especificada"}</h3>
          <p>Género: ${m.gender || "No especificado"}</p>
          <p>Intereses: ${interests}</p>
        </div>
      `;
    }
  } catch (err) {
    console.error(err);
    alert("Error al cargar matches.");
  }
}

async function initLastMatchCount() {
  try {
    const name = await getCurrentUserName();
    const res = await fetch(`/matches/${encodeURIComponent(name)}`, { credentials: "include" });
    if (!res.ok) return;
    const matches = await res.json();
    lastMatchCount = matches.length;
  } catch (err) {
    console.error(err);
  }
}

async function checkNewMatches() {
  try {
    const name = await getCurrentUserName();
    const res = await fetch(`/matches/${encodeURIComponent(name)}`, { credentials: "include" });
    if (!res.ok) throw new Error("No se pudo cargar los matches");
    const matches = await res.json();

    if (matches.length > lastMatchCount) {
      alert("¡Tienes nuevos matches!");
      lastMatchCount = matches.length;
      // Opcional: actualizar UI
    }
  } catch (err) {
    console.error(err);
  }
}

// Variable global
let lastMatchCount = 0;

window.onload = async () => {
  await initLastMatchCount();
  await loadMatches();
  setInterval(checkNewMatches, 60000);
};
