const btnLlamar = document.getElementById("btn-llamar");
const btnColgar = document.getElementById("btn-colgar");
const btnAceptar = document.getElementById("btn-aceptar");
const btnRechazar = document.getElementById("btn-rechazar");
const overlay = document.getElementById("llamada");
const banner = document.getElementById("entrada");
const entradaTexto = document.getElementById("entrada-texto");
const callStatus = document.getElementById("call-status");
const videoLocal = document.getElementById("local");
const videoRemoto = document.getElementById("remoto");

let callId = null;
let peer = null;
let localStream = null;
let iceAfter = 0;
let pollTimer = null;
let pendingIce = [];
let remoteReady = false;

function csrf() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : "";
}

function jsonHeaders() {
  return {
    "Content-Type": "application/json",
    "X-CSRFToken": csrf(),
  };
}

async function api(url, options) {
  const respuesta = await fetch(url, { credentials: "same-origin", ...options });
  const data = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    throw new Error(data.error || "Error de llamada");
  }
  return data;
}

function sdpLines(sdp) {
  return String(sdp || "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);
}

function sdpFromRemote(payload) {
  if (payload && Array.isArray(payload.lines) && payload.lines.length > 0) {
    return `${payload.lines.join("\r\n")}\r\n`;
  }
  return `${sdpLines(payload && payload.sdp).join("\r\n")}\r\n`;
}

function sdpBody(description) {
  return {
    type: description.type,
    sdp: description.sdp,
    lines: sdpLines(description.sdp),
  };
}

function mostrarOverlay(texto) {
  overlay.hidden = false;
  callStatus.textContent = texto;
}

function ocultarBanner() {
  banner.hidden = true;
}

function estadoConexion(estado) {
  if (estado === "connected" || estado === "completed") {
    callStatus.textContent = "En llamada";
  } else if (estado === "checking" || estado === "connecting") {
    callStatus.textContent = "Conectando…";
  } else if (estado === "failed" || estado === "disconnected") {
    callStatus.textContent = "No se pudo conectar. Reintenta la llamada.";
  }
}

async function detener() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  if (peer) {
    peer.close();
    peer = null;
  }
  if (localStream) {
    localStream.getTracks().forEach((track) => track.stop());
    localStream = null;
  }
  videoLocal.srcObject = null;
  videoRemoto.srcObject = null;
  overlay.hidden = true;
  callId = null;
  pendingIce = [];
  remoteReady = false;
}

async function mediaLocal() {
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  videoLocal.srcObject = localStream;
  return localStream;
}

function publicarIce(candidate) {
  if (!callId || !candidate || !candidate.candidate) {
    return;
  }
  api(`/api/llamadas/${callId}/ice`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({
      candidate: candidate.candidate,
      sdpMid: candidate.sdpMid,
      sdpMLineIndex: candidate.sdpMLineIndex,
    }),
  }).catch(() => undefined);
}

async function vaciarIce() {
  if (!peer || !remoteReady) {
    return;
  }
  const cola = pendingIce;
  pendingIce = [];
  for (const item of cola) {
    await peer.addIceCandidate(item);
  }
}

function crearPeer() {
  const connection = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
  });
  connection.onicecandidate = (evento) => {
    publicarIce(evento.candidate);
  };
  connection.ontrack = (evento) => {
    if (evento.streams && evento.streams[0]) {
      videoRemoto.srcObject = evento.streams[0];
      return;
    }
    videoRemoto.srcObject = new MediaStream([evento.track]);
  };
  connection.oniceconnectionstatechange = () => {
    estadoConexion(connection.iceConnectionState);
  };
  connection.onconnectionstatechange = () => {
    estadoConexion(connection.connectionState);
  };
  return connection;
}

function asignarPistas(stream) {
  stream.getTracks().forEach((track) => peer.addTrack(track, stream));
}

async function publicarOferta() {
  const oferta = await peer.createOffer({ offerToReceiveAudio: true, offerToReceiveVideo: true });
  await peer.setLocalDescription(oferta);
  await api(`/api/llamadas/${callId}/oferta`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(sdpBody(oferta)),
  });
}

async function publicarRespuesta(oferta) {
  await peer.setRemoteDescription({ type: oferta.type, sdp: sdpFromRemote(oferta) });
  remoteReady = true;
  await vaciarIce();
  const respuesta = await peer.createAnswer();
  await peer.setLocalDescription(respuesta);
  await api(`/api/llamadas/${callId}/respuesta`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(sdpBody(respuesta)),
  });
}

async function aplicarIce() {
  if (!callId || !peer) {
    return;
  }
  const data = await api(`/api/llamadas/${callId}/ice?after=${iceAfter}`);
  for (const item of data.candidates || []) {
    iceAfter = item.id;
    const payload = {
      candidate: item.candidate,
      sdpMid: item.sdpMid,
      sdpMLineIndex: item.sdpMLineIndex,
    };
    if (remoteReady) {
      await peer.addIceCandidate(payload);
    } else {
      pendingIce.push(payload);
    }
  }
}

async function sincronizar() {
  if (!callId) {
    return;
  }
  const data = await api(`/api/llamadas/${callId}`);
  if (data.status === "ended" || data.status === "rejected") {
    await detener();
    return;
  }
  if (peer && data.answer && !remoteReady) {
    await peer.setRemoteDescription({
      type: data.answer.type,
      sdp: sdpFromRemote(data.answer),
    });
    remoteReady = true;
    await vaciarIce();
    callStatus.textContent = "En llamada";
  }
  await aplicarIce();
}

function iniciarPoll() {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
  pollTimer = setInterval(() => {
    sincronizar().catch(() => undefined);
  }, 800);
}

async function iniciarComoCaller(para) {
  const creada = await api("/api/llamadas", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ para }),
  });
  callId = creada.id;
  iceAfter = 0;
  remoteReady = false;
  mostrarOverlay("Llamando… espera a que acepten");
  const stream = await mediaLocal();
  peer = crearPeer();
  asignarPistas(stream);
  await publicarOferta();
  iniciarPoll();
}

async function iniciarComoCallee(id, oferta) {
  callId = id;
  iceAfter = 0;
  remoteReady = false;
  mostrarOverlay("Conectando…");
  const stream = await mediaLocal();
  peer = crearPeer();
  asignarPistas(stream);
  await publicarRespuesta(oferta);
  callStatus.textContent = "En llamada";
  iniciarPoll();
}

btnLlamar.addEventListener("click", async () => {
  const para = window.contactoActual;
  if (!para) {
    return;
  }
  try {
    await iniciarComoCaller(para);
  } catch (error) {
    mostrarOverlay(error.message);
  }
});

btnColgar.addEventListener("click", async () => {
  if (callId) {
    await api(`/api/llamadas/${callId}/colgar`, {
      method: "POST",
      headers: jsonHeaders(),
    }).catch(() => undefined);
  }
  await detener();
});

async function esperarOferta(id) {
  for (let intento = 0; intento < 40; intento += 1) {
    const detalle = await api(`/api/llamadas/${id}`);
    if (detalle.offer && detalle.offer.sdp) {
      return detalle.offer;
    }
    await new Promise((resolve) => {
      setTimeout(resolve, 400);
    });
  }
  throw new Error("No llegó la oferta de video. Vuelve a llamar.");
}

btnAceptar.addEventListener("click", async () => {
  const id = banner.dataset.callId;
  ocultarBanner();
  mostrarOverlay("Conectando…");
  try {
    const oferta = await esperarOferta(id);
    await iniciarComoCallee(id, oferta);
  } catch (error) {
    mostrarOverlay(error.message);
  }
});

btnRechazar.addEventListener("click", async () => {
  const id = banner.dataset.callId;
  ocultarBanner();
  if (id) {
    await api(`/api/llamadas/${id}/rechazar`, {
      method: "POST",
      headers: jsonHeaders(),
    }).catch(() => undefined);
  }
});

async function revisarEntrantes() {
  if (callId) {
    return;
  }
  const data = await api("/api/llamadas/entrantes");
  const primera = (data.calls || [])[0];
  if (!primera) {
    ocultarBanner();
    return;
  }
  banner.hidden = false;
  banner.dataset.callId = primera.id;
  entradaTexto.textContent = `Llamada de ${primera.peer}`;
}

setInterval(() => {
  revisarEntrantes().catch(() => undefined);
}, 1000);
