let currentState = 'standby';
let selectedTheme = 'auto';
let lipSyncInterval = null;
let ws = null;

// --- 1. AMBIENT CANVAS (STARS + RAIN PARTICLES) ---
const canvas = document.getElementById('ambient-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  initParticles();
}
window.addEventListener('resize', resizeCanvas);

function initParticles() {
  particles = Array.from({ length: 60 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    len: Math.random() * 18 + 10,
    speed: Math.random() * 5 + 3,
    alpha: Math.random() * 0.7 + 0.2
  }));
}
resizeCanvas();

function changeTheme(val) {
  selectedTheme = val;
  applyTheme();
}

function applyTheme() {
  let activeTheme = selectedTheme;
  if (activeTheme === 'auto') {
    const hour = new Date().getHours();
    if (hour >= 6 && hour < 18) activeTheme = 'day';
    else if (hour >= 18 && hour < 20) activeTheme = 'golden';
    else activeTheme = 'night';
  }

  const isSleeping = currentState.toLowerCase() === 'standby' ? 'sleeping' : '';
  document.body.className = `theme-${activeTheme} ${isSleeping}`.trim();
}

function renderAmbient() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const isRain = document.body.classList.contains('theme-rain');
  const isGolden = document.body.classList.contains('theme-golden');

  if (isRain) {
    ctx.strokeStyle = '#60a5fa';
    ctx.lineWidth = 1.2;
    particles.forEach(p => {
      ctx.globalAlpha = p.alpha;
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(p.x - 2, p.y + p.len);
      ctx.stroke();
      p.y += p.speed * 2.2;
      p.x -= 0.5;
      if (p.y > canvas.height) { p.y = -10; p.x = Math.random() * canvas.width; }
    });
  } else {
    ctx.fillStyle = isGolden ? '#f59e0b' : '#00f2fe';
    particles.forEach(p => {
      ctx.globalAlpha = p.alpha;
      ctx.beginPath();
      ctx.arc(p.x, p.y, Math.min(p.len / 10, 2), 0, Math.PI * 2);
      ctx.fill();
      p.y -= p.speed * 0.15;
      if (p.y < 0) { p.y = canvas.height; p.x = Math.random() * canvas.width; }
    });
  }
  requestAnimationFrame(renderAmbient);
}
renderAmbient();

// --- 2. INTERACTIVE PETTING & MINI DRONE ---
function patHead() {
  const robot = document.getElementById('robot-avatar');
  robot.classList.add('happy');
  document.getElementById('aura-text').innerText = "Hehe! That tickles! ^_^";
  spinDrone();
  setTimeout(() => robot.classList.remove('happy'), 2500);
}

function petDrone() {
  spinDrone();
  document.getElementById('aura-text').innerText = "Spark: *Happy Drone Chirps!*";
}

function spinDrone() {
  const drone = document.getElementById('mini-drone');
  drone.classList.remove('spin');
  void drone.offsetWidth;
  drone.classList.add('spin');
}

// --- 3. KINETIC AUDIO LIP-SYNC ---
function triggerLipSync() {
  if (lipSyncInterval) clearInterval(lipSyncInterval);
  const eyes = document.querySelectorAll('.robot-eye');
  lipSyncInterval = setInterval(() => {
    if (currentState.toLowerCase() !== 'speaking') {
      clearInterval(lipSyncInterval);
      eyes.forEach(eye => eye.style.height = '');
      return;
    }
    const amp = Math.floor(Math.random() * 60) + 25;
    eyes.forEach(eye => eye.style.height = `${amp}px`);
  }, 70);
}

// --- 4. GAZE TRACKING ---
setInterval(() => {
  const s = currentState.toLowerCase();
  if (s === 'standby' || s === 'speaking') {
    document.documentElement.style.setProperty('--gaze-x', '0px');
    document.documentElement.style.setProperty('--gaze-y', '0px');
    document.documentElement.style.setProperty('--head-tilt', '0deg');
    return;
  }
  const tilt = (Math.random() - 0.5) * 8;
  const gx = (Math.random() - 0.5) * 24;
  const gy = (Math.random() - 0.5) * 16;
  document.documentElement.style.setProperty('--head-tilt', `${tilt}deg`);
  document.documentElement.style.setProperty('--gaze-x', `${gx}px`);
  document.documentElement.style.setProperty('--gaze-y', `${gy}px`);
}, 1800);

// --- 5. CLOCK & TICK LOOP ---
function updateClock() {
  const now = new Date();
  document.getElementById('digital-clock').innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  document.getElementById('digital-date').innerText = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();
  applyTheme();
}
setInterval(updateClock, 1000);
updateClock();

// --- 6. STATE CONTROLLER ---
function setAssistantState(state, userText = "", auraText = "") {
  currentState = state.toLowerCase();
  const robot = document.getElementById('robot-avatar');
  robot.className = 'robot-head ' + currentState;
  document.getElementById('companion-state').innerText = state.toUpperCase();
  applyTheme();

  if (userText) document.getElementById('user-text').innerText = userText;
  if (auraText) document.getElementById('aura-text').innerText = auraText;

  document.querySelectorAll('.robot-eye').forEach(eye => eye.style.height = '');
  if (currentState === 'speaking') {
    triggerLipSync();
    spinDrone();
  }
}

// --- 7. WEBSOCKET CLIENT ---
function connectWebSocket() {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
  
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    const dot = document.getElementById('status-dot');
    if (dot) dot.style.background = 'var(--eye-green)';
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.state) {
        setAssistantState(data.state, data.user_text || "", data.assistant_text || "");
      }

      if (data.cpu_temp !== undefined) {
        const temp = Math.round(data.cpu_temp);
        const cpu = Math.round(data.cpu_percent);
        const ram = Math.round(data.ram_percent);

        document.getElementById('val-temp').innerText = `${temp}°C`;
        document.getElementById('val-cpu').innerText = `${cpu}%`;
        document.getElementById('val-ram').innerText = `${ram}%`;

        if (vitalsChart) {
          vitalsChart.data.datasets[0].data.push(temp); vitalsChart.data.datasets[0].data.shift();
          vitalsChart.data.datasets[1].data.push(cpu); vitalsChart.data.datasets[1].data.shift();
          vitalsChart.data.datasets[2].data.push(ram); vitalsChart.data.datasets[2].data.shift();
          vitalsChart.update('none');
        }
      }
    } catch (err) {
      console.error("WebSocket message parse error:", err);
    }
  };

  ws.onclose = () => {
    const dot = document.getElementById('status-dot');
    if (dot) dot.style.background = 'var(--eye-magenta)';
    setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => ws.close();
}
connectWebSocket();

// --- 8. TELEMETRY & ACTIONS ---
let vitalsChart = null;
function initTelemetryChart() {
  const c = document.getElementById('vitalsChart').getContext('2d');
  vitalsChart = new Chart(c, {
    type: 'line',
    data: {
      labels: Array(15).fill(''),
      datasets: [
        { label: 'Temp (°C)', borderColor: '#ec4899', backgroundColor: 'rgba(236,72,153,0.1)', data: Array(15).fill(null), tension: 0.3, fill: true },
        { label: 'CPU %', borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', data: Array(15).fill(null), tension: 0.3, fill: true },
        { label: 'RAM %', borderColor: '#00f2fe', backgroundColor: 'rgba(0,242,254,0.1)', data: Array(15).fill(null), tension: 0.3, fill: true }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { min: 10, max: 100, grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#64748b' } }, x: { display: false } },
      plugins: { legend: { labels: { color: '#f8fafc', font: { size: 10 } } } }
    }
  });
}

function toggleTelemetry() {
  const modal = document.getElementById('telemetry-modal');
  const isFlex = modal.style.display === 'flex';
  modal.style.display = isFlex ? 'none' : 'flex';
  if (!isFlex && !vitalsChart) initTelemetryChart();
}

function triggerWake() {
  setAssistantState('listening', 'Wake trigger tapped...', 'Listening to you...');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "wake" }));
  }
}

function sendQuickPrompt(text) {
  setAssistantState('thinking', text, 'Thinking...');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "query", text: text }));
  }
}

function toggleMute() {
  setAssistantState('standby', 'Mute toggled.', 'Microphone inactive.');
  fetch('/api/mute', { method: 'POST' }).catch(() => {});
}