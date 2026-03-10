// script.js compartilhado entre as páginas

document.addEventListener('DOMContentLoaded', function() {
    // comportamento da página inicial (visitante)
    const form = document.getElementById('form-visita');
    if (form) {
        // se veio com qr_id na query, mostra imagem do QR e preenche campo oculto
        const params = new URLSearchParams(window.location.search);
        const qr_id = params.get('qr_id');
        if (qr_id) {
            document.getElementById('qr_id').value = qr_id;
            const img = document.getElementById('qr-img');
            img.src = `http://${window.location.host}/api/qrcode/${qr_id}`;
            img.style.display = '';
            document.getElementById('intro-text').textContent = 'Preencha seus dados e aguarde a autorização do morador.';
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                qr_id: document.getElementById('qr_id').value,
                nome: document.getElementById('nome').value,
                placa: document.getElementById('placa').value,
                destino: document.getElementById('destino').value
            };
            const response = await fetch(`http://${window.location.host}/api/iniciar_visita`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (result.visita_id) {
                document.getElementById('status-msg').textContent = 'Visita registrada! Aguarde autorização.';
                iniciarGPS(result.visita_id);
            } else if (result.erro) {
                alert(result.erro);
            }
        });
    }

    // Página de monitoramento do porteiro
    if (document.getElementById('map')) {
        carregarMapa();
        setInterval(atualizarVisitasPorteiro, 5000);
    }

    // Página do morador (autorizar visitantes)
    const moradorTokenInput = document.getElementById('morador-token');
    if (moradorTokenInput) {
        // token pode vir pela query ou ser digitado
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        if (token) {
            moradorTokenInput.value = token;
            carregarVisitasPendentes(token);
        }
        document.getElementById('btn-carregar-visitas').addEventListener('click', () => {
            carregarVisitasPendentes(moradorTokenInput.value);
        });
    }
});

// Enviar localização GPS a cada 10 segundos
function iniciarGPS(visitaId) {
    if (!navigator.geolocation) {
        alert('Geolocalização não suportada');
        return;
    }
    setInterval(() => {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const data = {
                visita_id: visitaId,
                lat: pos.coords.latitude,
                lng: pos.coords.longitude
            };
            await fetch(`http://${window.location.host}/api/atualizar_localizacao`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }, (err) => {
            console.error('Erro GPS:', err);
        });
    }, 10000);
}

// Funções para o monitoramento do porteiro
let map;
let markers = {};

function carregarMapa() {
    map = L.map('map').setView([-23.5505, -46.6333], 13); // Centro SP
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    atualizarVisitasPorteiro();
}

async function atualizarVisitasPorteiro() {
    const response = await fetch(`http://${window.location.host}/api/visitas_ativas_porteiro`);
    const visitas = await response.json();
    const lista = document.getElementById('visitas-lista');
    lista.innerHTML = '';
    visitas.forEach(v => {
        if (v.latitude && v.longitude) {
            if (markers[v.id]) {
                markers[v.id].setLatLng([v.latitude, v.longitude]);
            } else {
                const marker = L.marker([v.latitude, v.longitude]).addTo(map);
                marker.bindPopup(`<b>${v.nome}</b><br>Destino: ${v.destino}<br>Status: ${v.status}`);
                markers[v.id] = marker;
            }
        }
        const li = document.createElement('li');
        li.textContent = `${v.nome} (${v.status}) - ${v.destino}`;
        lista.appendChild(li);
    });
}

// Funções do morador
async function carregarVisitasPendentes(token) {
    const resp = await fetch(`http://${window.location.host}/api/morador/visitas_pendentes/${token}`);
    if (resp.status !== 200) {
        alert('Token inválido');
        return;
    }
    const visitas = await resp.json();
    const cont = document.getElementById('visitas-pendentes');
    cont.innerHTML = '';
    visitas.forEach(v => {
        const div = document.createElement('div');
        div.innerHTML = `<strong>${v.nome}</strong> - ${v.destino} ` +
                        `<button onclick="autorizar(${v.id}, '${token}')">Autorizar</button>`;
        cont.appendChild(div);
    });
}

async function autorizar(visitaId, token) {
    const resp = await fetch(`http://${window.location.host}/api/morador/liberar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ visita_id: visitaId, token })
    });
    const result = await resp.json();
    if (result.status === 'liberado') {
        alert('Visita liberada!');
        carregarVisitasPendentes(token);
    } else {
        alert(result.erro || 'Erro');
    }
}
