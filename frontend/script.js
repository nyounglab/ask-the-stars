/**
 * 별들에게 물어봐! - 프론트엔드 스크립트
 * 화면 전환 + 천궁도 로딩 + 편지 메타포 결과
 */

const API_URL = '';

// DOM
const form = document.getElementById('birthInfoForm');
const submitBtn = document.getElementById('submitBtn');
const loadingText = document.getElementById('loadingText');
const errorMessage = document.getElementById('errorMessage');
const chartData = document.getElementById('chartData');
const serverBanner = document.getElementById('serverBanner');
const serverBannerMessage = document.getElementById('serverBannerMessage');
const letterContent = document.getElementById('letterContent');

// 로딩 메시지
const LOADING_MESSAGES = [
    '별들의 배치를 읽고 있습니다',
    '행성들의 궤도를 따라가고 있습니다',
    '하우스의 경계를 가늠하고 있습니다',
    '천체 사이의 대화를 듣고 있습니다',
    '차트 위에 드리운 패턴을 읽고 있습니다',
    '별자리가 품은 이야기를 풀어내고 있습니다',
    '당신만의 별 지도를 그리고 있습니다',
];

// 카테고리 매핑
const SECTIONS = {
    '종합':     { key: 'overview',    icon: '✨', label: '종합 운세' },
    '성격':     { key: 'personality', icon: '🎭', label: '성격' },
    '커리어':   { key: 'career',      icon: '💼', label: '커리어' },
    '연애':     { key: 'love',        icon: '💕', label: '연애' },
    '건강':     { key: 'health',      icon: '💪', label: '건강' },
    '재물':     { key: 'wealth',      icon: '💰', label: '재물' },
    '관계':     { key: 'relations',   icon: '🤝', label: '관계' },
    '인생흐름': { key: 'lifeflow',    icon: '🌊', label: '인생 흐름' },
};

let loadingInterval = null;
let progressInterval = null;
let lastFormData = null;

// ================================================================
// 화면 전환 시스템
// ================================================================
function setScreen(screenName) {
    document.body.setAttribute('data-screen', screenName);
    window.scrollTo(0, 0);
}

// ---- 폼 제출 ----
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = {
        name: document.getElementById('name').value.trim(),
        birthdate: document.getElementById('birthdate').value,
        birthtime: document.getElementById('birthtime').value,
        birthplace: document.getElementById('birthplace').value.trim(),
    };
    lastFormData = formData;
    await analyzeChart(formData);
});

// ---- 탭 전환 ----
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const category = btn.dataset.category;
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`panel-${category}`).classList.add('active');

    });
});

// ---- 탭 키보드 내비게이션 ----
document.querySelector('.category-tabs').addEventListener('keydown', (e) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    const tabs = Array.from(document.querySelectorAll('.tab-btn'));
    const currentIndex = tabs.indexOf(document.activeElement);
    if (currentIndex === -1) return;
    e.preventDefault();
    let newIndex;
    switch (e.key) {
        case 'ArrowRight': newIndex = (currentIndex + 1) % tabs.length; break;
        case 'ArrowLeft':  newIndex = (currentIndex - 1 + tabs.length) % tabs.length; break;
        case 'Home':       newIndex = 0; break;
        case 'End':        newIndex = tabs.length - 1; break;
    }
    tabs[newIndex].focus();
    tabs[newIndex].click();
});

// ================================================================
// API 호출
// ================================================================
async function analyzeChart(formData) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 130000);

    try {
        showLoading();
        submitBtn.disabled = true;

        const response = await fetch(`${API_URL}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
            signal: controller.signal,
        });

        if (!response.ok) {
            let detail = '서버 오류가 발생했습니다';
            try {
                const errorData = await response.json();
                detail = errorData.detail || detail;
            } catch (_) {}
            throw new Error(detail);
        }

        const result = await response.json();
        if (result.success) {
            displayResult(result, formData);
        } else {
            throw new Error(result.error || '분석 중 오류가 발생했습니다');
        }
    } catch (error) {
        console.error('에러:', error);
        showError(friendlyErrorMessage(error));
    } finally {
        clearTimeout(timeoutId);
        hideLoading();
        submitBtn.disabled = false;
    }
}

function friendlyErrorMessage(error) {
    if (error.name === 'AbortError') {
        return '요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.';
    }
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return '서버와 연결할 수 없습니다. 인터넷 연결을 확인해주세요.';
    }
    return error.message;
}

// ================================================================
// AI 응답 파싱
// ================================================================
function parseInterpretation(text) {
    const result = {};
    const parts = text.split(/===(\S+)===/);

    for (let i = 1; i < parts.length; i += 2) {
        const name = parts[i].trim();
        const content = (parts[i + 1] || '').trim();
        if (SECTIONS[name]) {
            const titleMatch = content.match(/^###\s*(.+)/m);
            const title = titleMatch ? titleMatch[1].trim() : name;
            const body = content.replace(/^###\s*.+\n?/, '').trim();
            result[name] = { title, body };
        }
    }
    return result;
}

function formatMarkdown(text) {
    if (!text) return '';
    let f = text;
    f = f.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    f = f.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    f = f.replace(/^- (.+)$/gm, '<li>$1</li>');
    f = f.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
    f = f.replace(/\n/g, '<br>');
    f = f.replace(/<br>(<\/?(?:h3|ul|li)>)/g, '$1');
    f = f.replace(/(<\/?(?:h3|ul|li)>)<br>/g, '$1');
    return f;
}

// ================================================================
// 결과 렌더링
// ================================================================
function displayResult(result, formData) {
    chartData.textContent = result.chart_data || '';

    // 요약 헤더: 이름 + 생년월일시 + 출생지
    const dateStr = formData.birthdate.replace(/-/g, '. ');
    const sections = parseInterpretation(result.interpretation || '');
    document.getElementById('resultSummary').textContent =
        `${formData.name} / ${dateStr} / ${formData.birthtime} / ${formData.birthplace}`;

    const hasValid = Object.keys(sections).length >= 3;

    if (hasValid) {
        for (const [sectionName, info] of Object.entries(SECTIONS)) {
            const panel = document.getElementById(`panel-${info.key}`);
            const data = sections[sectionName];

            if (data) {
                let warning = '';
                if (info.key === 'overview' && lastFormData && lastFormData.birthtime === '12:00') {
                    warning = '<div class="birthtime-warning">'
                        + '출생 시간이 12:00으로 입력되었습니다. '
                        + '정확한 출생 시간을 모를 경우 상승 별자리와 하우스 배치의 정확도가 낮을 수 있습니다.'
                        + '</div>';
                }
                panel.innerHTML = DOMPurify.sanitize(
                    warning
                    + '<div class="result-card">'
                    + '  <div class="panel-header">'
                    + '    <span class="panel-emoji">' + info.icon + '</span>'
                    + '    <h3 class="panel-title">' + data.title + '</h3>'
                    + '  </div>'
                    + '  <div class="panel-body">' + formatMarkdown(data.body) + '</div>'
                    + '</div>'
                );
            } else {
                panel.innerHTML = '<div class="result-card"><p class="panel-body" style="color:var(--text-muted)">이 카테고리의 데이터가 없습니다.</p></div>';
            }
        }
        document.querySelector('.category-tabs').style.display = 'flex';
    } else {
        const fallback = document.getElementById('panel-overview');
        let warning = '';
        if (lastFormData && lastFormData.birthtime === '12:00') {
            warning = '<div class="birthtime-warning">'
                + '출생 시간이 12:00으로 입력되었습니다. '
                + '정확한 출생 시간을 모를 경우 상승 별자리와 하우스 배치의 정확도가 낮을 수 있습니다.'
                + '</div>';
        }
        fallback.innerHTML = DOMPurify.sanitize(
            warning
            + '<div class="result-card">'
            + '  <div class="panel-body">' + formatMarkdown(result.interpretation || '') + '</div>'
            + '</div>'
        );
        document.querySelector('.category-tabs').style.display = 'none';
    }

    // 첫 번째 탭 초기화
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
    });
    const firstTab = document.querySelector('.tab-btn[data-category="overview"]');
    firstTab.classList.add('active');
    firstTab.setAttribute('aria-selected', 'true');

    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-overview').classList.add('active');

    showResult();
}

// ================================================================
// 로딩 (천궁도 애니메이션)
// ================================================================
function showLoading() {
    setScreen('loading');

    // 프로그레스 바 리셋
    const progressBar = document.getElementById('loadingProgressBar');
    if (progressBar) {
        progressBar.style.transition = 'none';
        progressBar.style.width = '0%';
        progressBar.offsetHeight; // 리플로우
        progressBar.style.transition = 'width 0.5s ease-out';
    }

    // 프로그레스: 천천히 90%까지 (완료 시 100%로 점프)
    let progress = 0;
    progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 3 + 0.5;
            if (progress > 90) progress = 90;
            if (progressBar) progressBar.style.width = progress + '%';
        }
    }, 800);

    // 로딩 메시지 순환
    let msgIndex = 0;
    loadingText.textContent = LOADING_MESSAGES[0];
    loadingText.style.opacity = '1';
    loadingInterval = setInterval(() => {
        msgIndex = (msgIndex + 1) % LOADING_MESSAGES.length;
        loadingText.style.opacity = '0';
        setTimeout(() => {
            loadingText.textContent = LOADING_MESSAGES[msgIndex];
            loadingText.style.opacity = '1';
        }, 300);
    }, 3500);
}

function hideLoading() {
    if (loadingInterval) { clearInterval(loadingInterval); loadingInterval = null; }
    if (progressInterval) { clearInterval(progressInterval); progressInterval = null; }

    // 프로그레스 100%로 채우기
    const progressBar = document.getElementById('loadingProgressBar');
    if (progressBar) progressBar.style.width = '100%';
}

// ================================================================
// 결과 화면
// ================================================================
function showResult() {
    setScreen('result');
}

// ================================================================
// 에러
// ================================================================
function showError(message) {
    errorMessage.textContent = message;
    setScreen('error');
}

async function retryLastRequest() {
    if (lastFormData) {
        await analyzeChart(lastFormData);
    } else {
        setScreen('form');
    }
}

// ================================================================
// 리셋
// ================================================================
function resetForm() {
    form.reset();
    setScreen('form');
}

// ================================================================
// 서버 배너
// ================================================================
function showServerBanner(message) {
    serverBannerMessage.textContent = message;
    serverBanner.style.display = 'block';
}

// ================================================================
// 버튼 이벤트 리스너
// ================================================================
document.getElementById('retryBtn').addEventListener('click', () => retryLastRequest());
document.getElementById('resetBtn').addEventListener('click', resetForm);
document.getElementById('backBtn').addEventListener('click', () => setScreen('form'));

// ================================================================
// 초기화
// ================================================================
window.addEventListener('DOMContentLoaded', async () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('birthdate').max = today;

    try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) {
            showServerBanner('서버가 응답하지 않습니다.');
        }
    } catch (error) {
        showServerBanner('백엔드 서버와 연결할 수 없습니다. 서버를 시작해주세요.');
    }
});
