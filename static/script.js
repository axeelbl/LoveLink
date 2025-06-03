async function getRecommendations() {
  const name = document.getElementById("rec-name").value;
  const res = await fetch(`/recommendations/${name}`, {
    credentials: "include"
  });
  const data = await res.json();

  const list = document.getElementById("recommendation-list");
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

function logout() {
  fetch("/logout", {
    method: "GET",
    credentials: "include"
  }).then(() => {
    window.location.href = "/login-page";
  });
}