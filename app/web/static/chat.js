const lista = document.getElementById("mensajes");
const form = document.getElementById("enviar");
const texto = document.getElementById("texto");
const boton = form.querySelector("button");
const aviso = document.getElementById("aviso");
const agregar = document.getElementById("agregar");
const nuevoContacto = document.getElementById("nuevo-contacto");
const csrfMeta = document.querySelector('meta[name="csrf-token"]');
let actual = null;
let espera = 2500;

function tokenCsrf() {
  return csrfMeta ? csrfMeta.content : "";
}

function mostrarAviso(mensaje) {
  aviso.hidden = !mensaje;
  aviso.textContent = mensaje || "";
}

function renderMensajes(items) {
  lista.replaceChildren();
  items.forEach((item) => {
    const bubble = document.createElement("div");
    bubble.className = item.mine ? "bubble mine" : "bubble";
    bubble.textContent = item.body;
    lista.appendChild(bubble);
  });
  lista.scrollTop = lista.scrollHeight;
}

async function cargar() {
  if (!actual) {
    return;
  }
  try {
    const respuesta = await fetch(`/api/mensajes?con=${encodeURIComponent(actual)}`);
    if (respuesta.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!respuesta.ok) {
      espera = Math.min(espera * 2, 15000);
      return;
    }
    espera = 2500;
    const data = await respuesta.json();
    renderMensajes(data.messages || []);
  } catch {
    espera = Math.min(espera * 2, 15000);
  }
}

document.querySelectorAll(".contact").forEach((botonContacto) => {
  botonContacto.addEventListener("click", () => {
    document.querySelectorAll(".contact").forEach((el) => el.classList.remove("active"));
    botonContacto.classList.add("active");
    actual = botonContacto.dataset.user;
    window.contactoActual = actual;
    const etiqueta = document.getElementById("titulo-texto");
    if (etiqueta) {
      etiqueta.textContent = actual;
    }
    const btnLlamar = document.getElementById("btn-llamar");
    if (btnLlamar) {
      btnLlamar.disabled = false;
    }
    texto.disabled = false;
    boton.disabled = false;
    texto.focus();
    cargar();
  });
});

agregar.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const username = nuevoContacto.value.trim();
  if (!username) {
    return;
  }
  const respuesta = await fetch("/api/contactos", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": tokenCsrf(),
    },
    body: JSON.stringify({ username }),
  });
  const data = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    mostrarAviso(data.error || "No se pudo agregar el contacto.");
    return;
  }
  mostrarAviso("");
  window.location.reload();
});

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  if (!actual || !texto.value.trim()) {
    return;
  }
  try {
    const respuesta = await fetch("/api/mensajes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": tokenCsrf(),
      },
      body: JSON.stringify({ para: actual, texto: texto.value }),
    });
    if (!respuesta.ok) {
      const data = await respuesta.json().catch(() => ({}));
      mostrarAviso(data.error || "No se pudo enviar el mensaje.");
      return;
    }
    texto.value = "";
    mostrarAviso("");
    await cargar();
  } catch {
    mostrarAviso("Error de red al enviar.");
  }
});

function programar() {
  setTimeout(async () => {
    await cargar();
    programar();
  }, espera);
}

programar();
