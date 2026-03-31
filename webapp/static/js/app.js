// --- Telegram WebApp ---
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

const API_BASE = '';
const initData = tg?.initData || '';
const DEV_USER_ID = '12345'; // fallback for dev

function apiHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (initData) {
        headers['X-Telegram-Init-Data'] = initData;
    } else {
        headers['X-User-Id'] = DEV_USER_ID;
    }
    return headers;
}

async function api(path, options = {}) {
    const res = await fetch(API_BASE + path, {
        headers: apiHeaders(),
        ...options,
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// --- State ---
let emotions = [];
let selectedEmotion = null;
let currentIntensity = 5;
let currentDate = new Date();
let currentPeriod = 'day';
let chartInstance = null;

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
    await loadEmotions();
    renderEmotionGrid();
    setupTabs();
    setupIntensitySlider();
    navigateToTab('log');
});

// --- Load emotions ---
async function loadEmotions() {
    try {
        emotions = await api('/api/emotions');
    } catch (e) {
        console.error('Failed to load emotions:', e);
        emotions = [];
    }
}

// --- Tab navigation ---
function setupTabs() {
    document.querySelectorAll('.tab-item').forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            navigateToTab(target);
        });
    });
}

function navigateToTab(tab) {
    document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    document.querySelector(`.tab-item[data-tab="${tab}"]`)?.classList.add('active');
    document.getElementById(`page-${tab}`)?.classList.add('active');

    if (tab === 'history') loadHistory();
    if (tab === 'stats') loadStats();
    if (tab === 'summary') loadSummary();
}

// --- Emotion grid ---
function renderEmotionGrid() {
    const grid = document.getElementById('emotion-grid');
    if (!grid) return;

    grid.innerHTML = emotions.map(e => `
        <button class="emotion-btn" data-emotion="${e.id}" onclick="selectEmotion('${e.id}')">
            <span class="emoji">${e.emoji}</span>
            <span class="label">${e.name}</span>
        </button>
    `).join('');
}

function selectEmotion(id) {
    selectedEmotion = id;
    document.querySelectorAll('.emotion-btn').forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.emotion === id);
    });
    updateSubmitButton();
}

// --- Intensity slider ---
function setupIntensitySlider() {
    const slider = document.getElementById('intensity-slider');
    const value = document.getElementById('intensity-value');
    if (!slider) return;

    slider.addEventListener('input', () => {
        currentIntensity = parseInt(slider.value);
        value.textContent = currentIntensity;
    });
}

function updateSubmitButton() {
    const btn = document.getElementById('submit-btn');
    if (btn) btn.disabled = !selectedEmotion;
}

// --- Submit entry ---
async function submitEntry() {
    if (!selectedEmotion) return;

    const note = document.getElementById('entry-note')?.value?.trim() || '';
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.textContent = 'Сохраняю...';

    try {
        await api('/api/entries', {
            method: 'POST',
            body: JSON.stringify({
                emotion: selectedEmotion,
                intensity: currentIntensity,
                note: note,
            }),
        });

        showToast('Запись сохранена!');

        // Reset form
        selectedEmotion = null;
        currentIntensity = 5;
        document.querySelectorAll('.emotion-btn').forEach(b => b.classList.remove('selected'));
        document.getElementById('intensity-slider').value = 5;
        document.getElementById('intensity-value').textContent = '5';
        document.getElementById('entry-note').value = '';

        if (tg) tg.HapticFeedback?.impactOccurred('medium');
    } catch (e) {
        showToast('Ошибка сохранения');
        console.error(e);
    }

    btn.disabled = false;
    btn.textContent = 'Записать';
    updateSubmitButton();
}

// --- History ---
async function loadHistory() {
    const dateStr = formatDateISO(currentDate);
    const container = document.getElementById('history-entries');
    const dateLabel = document.getElementById('history-date-label');
    if (!container) return;

    dateLabel.textContent = formatDateRu(currentDate);
    container.innerHTML = '<div class="empty-state"><p>Загрузка...</p></div>';

    try {
        const entries = await api(`/api/entries/${dateStr}`);
        if (entries.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <p>Нет записей за этот день</p>
                </div>`;
            return;
        }

        const emoMap = Object.fromEntries(emotions.map(e => [e.id, e]));
        container.innerHTML = '<div class="timeline-line">' + entries.map(entry => {
            const emo = emoMap[entry.emotion] || { emoji: '❓', name: entry.emotion, color: '#999' };
            const time = entry.created_at?.substring(11, 16) || '';
            return `
                <div class="timeline-entry">
                    <div class="entry-item">
                        <div class="entry-emoji">${emo.emoji}</div>
                        <div class="entry-content">
                            <div class="entry-header">
                                <span class="entry-emotion-name">${emo.name}</span>
                                <span class="entry-time">${time}</span>
                            </div>
                            <div class="entry-intensity">
                                Интенсивность: ${entry.intensity}/10
                                <span class="entry-intensity-bar" style="width: ${entry.intensity * 10}%; background: ${emo.color}"></span>
                            </div>
                            ${entry.note ? `<div class="entry-note">${escapeHtml(entry.note)}</div>` : ''}
                        </div>
                        <button class="entry-delete" onclick="deleteEntry(${entry.id})" title="Удалить">×</button>
                    </div>
                </div>`;
        }).join('') + '</div>';
    } catch (e) {
        container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки</p></div>';
        console.error(e);
    }
}

function changeHistoryDate(delta) {
    currentDate.setDate(currentDate.getDate() + delta);
    loadHistory();
}

async function deleteEntry(id) {
    if (!confirm('Удалить запись?')) return;
    try {
        await api(`/api/entries/${id}`, { method: 'DELETE' });
        showToast('Запись удалена');
        loadHistory();
    } catch (e) {
        showToast('Ошибка удаления');
    }
}

// --- Stats ---
async function loadStats() {
    const periodTabs = document.querySelectorAll('.period-tab');
    periodTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.period === currentPeriod);
    });

    if (currentPeriod === 'day') await loadDayStats();
    else if (currentPeriod === 'week') await loadWeekStats();
    else await loadMonthStats();
}

function changePeriod(period) {
    currentPeriod = period;
    loadStats();
}

async function loadDayStats() {
    const dateStr = formatDateISO(currentDate);
    const statsContainer = document.getElementById('stats-content');
    const dateLabel = document.getElementById('stats-date-label');
    dateLabel.textContent = formatDateRu(currentDate);

    try {
        const data = await api(`/api/stats/day/${dateStr}`);
        renderDayChart(data);
        renderStatPills(data.stats);
    } catch (e) {
        statsContainer.innerHTML = '<div class="empty-state"><p>Ошибка загрузки</p></div>';
    }
}

async function loadWeekStats() {
    const dateStr = formatDateISO(currentDate);
    const dateLabel = document.getElementById('stats-date-label');

    try {
        const data = await api(`/api/stats/week/${dateStr}`);
        dateLabel.textContent = `${formatDateShort(data.start)} — ${formatDateShort(data.end)}`;
        renderWeekChart(data);
        renderStatPills(data.overall);
    } catch (e) {
        console.error(e);
    }
}

async function loadMonthStats() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    const dateLabel = document.getElementById('stats-date-label');
    const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    dateLabel.textContent = `${monthNames[month - 1]} ${year}`;

    try {
        const data = await api(`/api/stats/month/${year}/${month}`);
        renderMonthChart(data);
        renderStatPills(data.overall);
    } catch (e) {
        console.error(e);
    }
}

function changeStatsDate(delta) {
    if (currentPeriod === 'day') {
        currentDate.setDate(currentDate.getDate() + delta);
    } else if (currentPeriod === 'week') {
        currentDate.setDate(currentDate.getDate() + delta * 7);
    } else {
        currentDate.setMonth(currentDate.getMonth() + delta);
    }
    loadStats();
}

// --- Chart rendering ---
function renderDayChart(data) {
    const ctx = document.getElementById('stats-chart');
    if (!ctx) return;

    destroyChart();
    const emoMap = Object.fromEntries(emotions.map(e => [e.id, e]));

    if (!data.entries || data.entries.length === 0) {
        document.getElementById('stats-chart-container').innerHTML =
            '<div class="empty-state"><div class="empty-icon">📊</div><p>Нет данных за этот день</p></div>';
        return;
    }

    // Ensure canvas exists
    ensureCanvas();

    const timeLabels = data.entries.map(e => e.created_at?.substring(11, 16) || '');
    const intensities = data.entries.map(e => e.intensity);
    const bgColors = data.entries.map(e => (emoMap[e.emotion]?.color || '#999') + '80');
    const borderColors = data.entries.map(e => emoMap[e.emotion]?.color || '#999');

    chartInstance = new Chart(document.getElementById('stats-chart'), {
        type: 'bar',
        data: {
            labels: timeLabels,
            datasets: [{
                label: 'Интенсивность',
                data: intensities,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 6,
            }],
        },
        options: chartOptions('Интенсивность эмоций в течение дня', 10),
    });
}

function renderWeekChart(data) {
    destroyChart();
    ensureCanvas();

    const emoMap = Object.fromEntries(emotions.map(e => [e.id, e]));
    const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

    // Build 7 days from start
    const startDate = new Date(data.start + 'T00:00:00');
    const labels = [];
    const dayKeys = [];
    for (let i = 0; i < 7; i++) {
        const d = new Date(startDate);
        d.setDate(d.getDate() + i);
        labels.push(dayNames[i]);
        dayKeys.push(formatDateISO(d));
    }

    // Get unique emotions across the week
    const allEmotions = new Set();
    for (const dayData of Object.values(data.daily_data || {})) {
        dayData.forEach(s => allEmotions.add(s.emotion));
    }

    const datasets = [];
    for (const emoId of allEmotions) {
        const emo = emoMap[emoId] || { name: emoId, color: '#999' };
        datasets.push({
            label: emo.name,
            data: dayKeys.map(dk => {
                const dayStats = (data.daily_data || {})[dk] || [];
                const found = dayStats.find(s => s.emotion === emoId);
                return found ? found.avg_intensity : 0;
            }),
            backgroundColor: emo.color + '80',
            borderColor: emo.color,
            borderWidth: 2,
            borderRadius: 4,
        });
    }

    chartInstance = new Chart(document.getElementById('stats-chart'), {
        type: 'bar',
        data: { labels, datasets },
        options: {
            ...chartOptions('Средняя интенсивность по дням', 10),
            plugins: {
                ...chartOptions('', 10).plugins,
                legend: { display: true, position: 'bottom', labels: { font: { size: 11 }, padding: 8 } },
            },
        },
    });
}

function renderMonthChart(data) {
    destroyChart();
    ensureCanvas();

    const emoMap = Object.fromEntries(emotions.map(e => [e.id, e]));

    // Pie/doughnut of overall emotions
    const overall = data.overall || [];
    if (overall.length === 0) {
        document.getElementById('stats-chart-container').innerHTML =
            '<div class="empty-state"><div class="empty-icon">📊</div><p>Нет данных за этот месяц</p></div>';
        return;
    }

    const labels = overall.map(s => {
        const e = emoMap[s.emotion];
        return e ? `${e.emoji} ${e.name}` : s.emotion;
    });
    const values = overall.map(s => s.count);
    const colors = overall.map(s => emoMap[s.emotion]?.color || '#999');

    chartInstance = new Chart(document.getElementById('stats-chart'), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors.map(c => c + '80'),
                borderColor: colors,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'bottom', labels: { font: { size: 11 }, padding: 8 } },
                title: { display: true, text: 'Распределение эмоций за месяц', font: { size: 14 } },
            },
        },
    });
}

function destroyChart() {
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
}

function ensureCanvas() {
    const container = document.getElementById('stats-chart-container');
    container.innerHTML = '<canvas id="stats-chart"></canvas>';
}

function chartOptions(title, maxY) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, max: maxY, ticks: { stepSize: 1 } },
            x: { grid: { display: false } },
        },
        plugins: {
            legend: { display: false },
            title: { display: !!title, text: title, font: { size: 14 } },
        },
    };
}

function renderStatPills(stats) {
    const container = document.getElementById('stats-pills');
    if (!container) return;

    const emoMap = Object.fromEntries(emotions.map(e => [e.id, e]));

    if (!stats || stats.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = stats.map(s => {
        const emo = emoMap[s.emotion] || { emoji: '❓', name: s.emotion };
        return `
            <div class="stat-pill">
                <span class="pill-emoji">${emo.emoji}</span>
                <span>${emo.name}</span>
                <span class="pill-count">×${s.count}</span>
                <span style="color: var(--text-secondary)">(${s.avg_intensity}/10)</span>
            </div>`;
    }).join('');
}

// --- Summary ---
async function loadSummary() {
    const periodTabs = document.querySelectorAll('#page-summary .period-tab');
    periodTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.period === currentPeriod);
    });

    const dateLabel = document.getElementById('summary-date-label');
    const textarea = document.getElementById('summary-text');
    let periodDate;

    if (currentPeriod === 'day') {
        periodDate = formatDateISO(currentDate);
        dateLabel.textContent = formatDateRu(currentDate);
    } else if (currentPeriod === 'week') {
        const d = new Date(currentDate);
        const day = d.getDay() || 7;
        d.setDate(d.getDate() - day + 1);
        periodDate = formatDateISO(d);
        const end = new Date(d);
        end.setDate(end.getDate() + 6);
        dateLabel.textContent = `${formatDateShort(formatDateISO(d))} — ${formatDateShort(formatDateISO(end))}`;
    } else {
        periodDate = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
        const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        dateLabel.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
    }

    textarea.dataset.periodType = currentPeriod;
    textarea.dataset.periodDate = periodDate;

    try {
        const data = await api(`/api/summary/${currentPeriod}/${periodDate}`);
        textarea.value = data.summary_text || '';
    } catch {
        textarea.value = '';
    }
}

async function saveSummary() {
    const textarea = document.getElementById('summary-text');
    const periodType = textarea.dataset.periodType;
    const periodDate = textarea.dataset.periodDate;
    const text = textarea.value.trim();

    if (!text) {
        showToast('Напишите что-нибудь');
        return;
    }

    try {
        await api('/api/summary', {
            method: 'POST',
            body: JSON.stringify({
                period_type: periodType,
                period_date: periodDate,
                summary_text: text,
            }),
        });
        showToast('Итог сохранён!');
        if (tg) tg.HapticFeedback?.impactOccurred('light');
    } catch (e) {
        showToast('Ошибка сохранения');
    }
}

function changeSummaryPeriod(period) {
    currentPeriod = period;
    loadSummary();
}

function changeSummaryDate(delta) {
    if (currentPeriod === 'day') {
        currentDate.setDate(currentDate.getDate() + delta);
    } else if (currentPeriod === 'week') {
        currentDate.setDate(currentDate.getDate() + delta * 7);
    } else {
        currentDate.setMonth(currentDate.getMonth() + delta);
    }
    loadSummary();
}

// --- Utils ---
function formatDateISO(d) {
    if (typeof d === 'string') d = new Date(d + 'T00:00:00');
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function formatDateRu(d) {
    const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
    const dayOfWeek = ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'];
    return `${d.getDate()} ${months[d.getMonth()]}, ${dayOfWeek[d.getDay()]}`;
}

function formatDateShort(isoStr) {
    const [y, m, d] = isoStr.split('-');
    return `${parseInt(d)}.${parseInt(m)}`;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showToast(msg) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}
