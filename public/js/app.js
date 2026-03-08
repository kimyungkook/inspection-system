/* ══════════════════════════════════════════════════════════════════
   검사기록관리 시스템 v01 - Main Application JS
   ══════════════════════════════════════════════════════════════════ */

const API_BASE = '/api';
let currentUser = null;
let authToken = null;
let currentPage = 'dashboard';
let currentSessionId = null;
let sessionStats = { total: 0, pass: 0, fail: 0 };
let scanHistory = [];
let weekChart = null;
let passChart = null;
let recordsCurrentPage = 1;
let cameraScanner = null;
let cameraActive = false;

// ─── 초기화 ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('irms_token');
  const user = localStorage.getItem('irms_user');
  if (token && user) {
    authToken = token;
    currentUser = JSON.parse(user);
    showApp();
  } else {
    showLogin();
  }
  updateDateTime();
  setInterval(updateDateTime, 1000);
});

function updateDateTime() {
  const el = document.getElementById('header-datetime');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleString('ko-KR', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  }
}

// ─── 인증 ─────────────────────────────────────────────────────────
async function doLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const alert = document.getElementById('login-alert');
  const btn = document.getElementById('login-btn');

  if (!username || !password) {
    showLoginError('아이디와 비밀번호를 입력하세요.');
    return;
  }

  btn.innerHTML = '<span class="loading-spinner me-2"></span>로그인 중...';
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('irms_token', authToken);
      localStorage.setItem('irms_user', JSON.stringify(currentUser));
      showApp();
    } else {
      showLoginError(data.message || '로그인 실패');
    }
  } catch (e) {
    showLoginError('서버에 연결할 수 없습니다.');
  } finally {
    btn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i> 로그인';
    btn.disabled = false;
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && document.getElementById('page-login').classList.contains('d-flex')) {
    doLogin();
  }
});

function showLoginError(msg) {
  const alert = document.getElementById('login-alert');
  alert.textContent = msg;
  alert.classList.remove('d-none');
  setTimeout(() => alert.classList.add('d-none'), 4000);
}

function togglePassword() {
  const input = document.getElementById('login-password');
  const icon = document.getElementById('pwd-eye');
  if (input.type === 'password') {
    input.type = 'text';
    icon.className = 'fas fa-eye-slash';
  } else {
    input.type = 'password';
    icon.className = 'fas fa-eye';
  }
}

async function doLogout() {
  try {
    await apiCall('/auth/logout', 'POST');
  } catch (e) {}
  authToken = null;
  currentUser = null;
  localStorage.removeItem('irms_token');
  localStorage.removeItem('irms_user');
  location.reload();
}

// ─── 앱 표시 ─────────────────────────────────────────────────────
function showLogin() {
  document.getElementById('page-login').classList.remove('d-none');
  document.getElementById('page-login').classList.add('d-flex');
  document.getElementById('page-app').classList.add('d-none');
}

function showApp() {
  document.getElementById('page-login').classList.add('d-none');
  document.getElementById('page-login').classList.remove('d-flex');
  document.getElementById('page-app').classList.remove('d-none');

  // 사용자 정보 표시
  document.getElementById('sidebar-username').textContent = currentUser.name;
  document.getElementById('header-username').textContent = currentUser.name;

  const roleMap = { admin: '관리자', manager: '담당자', inspector: '검사원', viewer: '조회자' };
  document.getElementById('sidebar-role').textContent = roleMap[currentUser.role] || currentUser.role;

  // 권한에 따른 메뉴 표시
  if (!['admin', 'manager'].includes(currentUser.role)) {
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
  }

  // 검사자 이름 자동 입력
  document.getElementById('insp-inspector').value = currentUser.name;

  // 오늘 날짜 기본값
  const today = new Date().toISOString().slice(0, 10);
  document.getElementById('insp-shipment-date').value = today;

  navigateTo('dashboard');
}

// ─── 네비게이션 ──────────────────────────────────────────────────
function navigateTo(page) {
  currentPage = page;

  // 모든 콘텐츠 섹션 숨기기
  document.querySelectorAll('.content-section').forEach(el => {
    el.classList.add('d-none');
  });

  // 현재 페이지 표시
  const target = document.getElementById(`content-${page}`);
  if (target) target.classList.remove('d-none');

  // 메뉴 active 상태
  document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
  const menuItem = document.querySelector(`.menu-item[data-page="${page}"]`);
  if (menuItem) menuItem.classList.add('active');

  // 브레드크럼
  const pageNames = {
    dashboard: '대시보드', inspection: '바코드 검사',
    products: '제품 등록', records: '검사 기록', users: '사용자 관리', settings: '시스템 설정'
  };
  document.getElementById('breadcrumb-current').textContent = pageNames[page] || page;

  // 모바일 사이드바 닫기
  closeSidebar();

  // 페이지별 데이터 로드
  if (page === 'dashboard') loadDashboard();
  else if (page === 'products') loadProducts();
  else if (page === 'records') { loadRecords(); }
  else if (page === 'users') loadUsers();
  else if (page === 'settings') loadSettings();
}

// ─── 사이드바 ─────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  sidebar.classList.toggle('open');
  if (sidebar.classList.contains('open')) {
    overlay.classList.remove('d-none');
  } else {
    overlay.classList.add('d-none');
  }
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (window.innerWidth < 992) {
    sidebar.classList.remove('open');
    overlay.classList.add('d-none');
  }
}

// ─── API 호출 ─────────────────────────────────────────────────────
async function apiCall(endpoint, method = 'GET', body = null, params = null) {
  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    if (qs) url += '?' + qs;
  }

  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    }
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  if (res.status === 401) {
    doLogout();
    throw new Error('인증이 만료되었습니다.');
  }
  return res.json();
}

// ─── 토스트 알림 ──────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const toastEl = document.getElementById('main-toast');
  document.getElementById('toast-message').textContent = msg;
  toastEl.className = `toast align-items-center text-white border-0 bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'}`;
  const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
  toast.show();
}

// ══════════════════════════════════════════════════════════════════
// 대시보드
// ══════════════════════════════════════════════════════════════════
async function loadDashboard() {
  try {
    const data = await apiCall('/inspections/stats');
    if (!data.success) return;

    const s = data.data;
    document.getElementById('stat-today-total').textContent = s.today_total || 0;
    document.getElementById('stat-today-pass').textContent = s.today_pass || 0;
    document.getElementById('stat-today-fail').textContent = s.today_fail || 0;
    document.getElementById('stat-active').textContent = s.active_sessions || 0;

    // 합격률
    const rate = s.today_total > 0 ? Math.round(s.today_pass / s.today_total * 100) : 0;
    document.getElementById('pass-rate-value').textContent = rate + '%';

    renderWeekChart(data.trend || []);
    renderPassRateChart(rate);
  } catch (e) {
    console.error(e);
  }
}

function renderWeekChart(trend) {
  const ctx = document.getElementById('weekChart');
  if (!ctx) return;
  if (weekChart) weekChart.destroy();

  const labels = trend.map(d => d.inspection_date);
  const pass = trend.map(d => d.pass_count);
  const fail = trend.map(d => d.fail_count);

  weekChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'PASS', data: pass, backgroundColor: 'rgba(5,122,85,.8)', borderRadius: 4 },
        { label: 'FAIL', data: fail, backgroundColor: 'rgba(200,30,30,.8)', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'top' } },
      scales: {
        x: { stacked: true },
        y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 } }
      }
    }
  });
}

function renderPassRateChart(rate) {
  const ctx = document.getElementById('passRateChart');
  if (!ctx) return;
  if (passChart) passChart.destroy();

  passChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['PASS', 'FAIL'],
      datasets: [{
        data: [rate, 100 - rate],
        backgroundColor: ['#057a55', '#c81e1e'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      cutout: '75%',
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

// ══════════════════════════════════════════════════════════════════
// 바코드 검사
// ══════════════════════════════════════════════════════════════════

async function startInspectionSession() {
  const material_code = document.getElementById('insp-material-code').value.trim();
  const model_name = document.getElementById('insp-model-name').value.trim();
  const lot_no = document.getElementById('insp-lot-long').value.trim();

  if (!material_code || !model_name || !lot_no) {
    showToast('자재코드, 모델명, LOT NO는 필수입니다.', 'error');
    return;
  }

  try {
    const data = await apiCall('/inspections/sessions', 'POST', {
      material_code,
      model_name,
      lot_no,
      shipment_date: document.getElementById('insp-shipment-date').value,
      total_quantity: parseInt(document.getElementById('insp-total-qty').value) || 0
    });

    if (data.success) {
      currentSessionId = data.session_id;
      sessionStats = { total: 0, pass: 0, fail: 0 };
      scanHistory = [];

      document.getElementById('session-progress-card').style.display = '';
      document.getElementById('session-progress-card').style.removeProperty('display');
      document.getElementById('btn-complete').disabled = false;
      document.getElementById('active-session-badge').style.display = '';

      updateProgressUI();
      showToast(`검사 세션 시작됨 (코드: ${data.session_code})`, 'success');

      // 스캔 입력 포커스
      setTimeout(() => document.getElementById('scan-input').focus(), 200);
    }
  } catch (e) {
    showToast('세션 시작 오류: ' + e.message, 'error');
  }
}

function handleScanInput(e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    processScan();
  }
}

async function processScan() {
  const scanned = document.getElementById('scan-input').value.trim();
  if (!scanned) return;

  // 현재 선택된 스캔 타입
  const scanType = document.querySelector('input[name="scan-type"]:checked').value;

  // 기대값 결정
  let expected = '';
  if (scanType === 'lot_long') {
    expected = document.getElementById('insp-lot-long').value.trim();
  } else if (scanType === 'lot_short') {
    expected = document.getElementById('insp-lot-short').value.trim();
  } else if (scanType === 'size') {
    expected = document.getElementById('insp-barcode-size').value.trim();
  }

  if (!expected) {
    showToast('해당 스캔 항목의 등록값이 없습니다. 먼저 제품 정보를 입력하세요.', 'error');
    document.getElementById('scan-input').value = '';
    return;
  }

  try {
    const data = await apiCall('/inspections/scan', 'POST', {
      session_id: currentSessionId,
      scanned_value: scanned,
      expected_value: expected,
      scan_type: scanType,
      material_code: document.getElementById('insp-material-code').value.trim(),
      model_name: document.getElementById('insp-model-name').value.trim(),
      lot_no: document.getElementById('insp-lot-long').value.trim(),
      shipment_date: document.getElementById('insp-shipment-date').value
    });

    if (data.success) {
      showScanResult(data);
      updateScanHistory(data, scanned);
      if (currentSessionId) {
        if (data.result === 'PASS') sessionStats.pass++;
        else sessionStats.fail++;
        sessionStats.total++;
        updateProgressUI();
      }
    }
  } catch (e) {
    showToast('스캔 처리 오류: ' + e.message, 'error');
  }

  document.getElementById('scan-input').value = '';
  document.getElementById('scan-input').focus();
}

function showScanResult(data) {
  const box = document.getElementById('scan-result');
  const icon = document.getElementById('result-icon');
  const badge = document.getElementById('result-badge');
  const isPass = data.result === 'PASS';

  box.className = `scan-result-box mt-3 ${isPass ? 'result-pass' : 'result-fail'}`;
  icon.innerHTML = isPass
    ? '<i class="fas fa-check-circle"></i>'
    : '<i class="fas fa-times-circle"></i>';
  badge.textContent = data.result;
  document.getElementById('result-scanned').textContent = data.scanned_value;
  document.getElementById('result-expected').textContent = data.expected_value;
  document.getElementById('result-seq').textContent = `#${data.sequence_no}`;

  box.classList.remove('d-none');

  // 페이지 플래시
  const content = document.getElementById('content-inspection');
  content.classList.add(isPass ? 'flash-pass' : 'flash-fail');
  setTimeout(() => content.classList.remove('flash-pass', 'flash-fail'), 700);

  // 진동 피드백 (모바일)
  if (navigator.vibrate) {
    navigator.vibrate(isPass ? [100] : [100, 50, 100]);
  }
}

function updateScanHistory(data, scanned) {
  const isPass = data.result === 'PASS';
  scanHistory.unshift({ seq: data.sequence_no, value: scanned, result: data.result });
  if (scanHistory.length > 30) scanHistory.pop();

  const list = document.getElementById('scan-history-list');
  const badge = document.getElementById('scan-count-badge');
  badge.textContent = scanHistory.length;

  list.innerHTML = scanHistory.map(item => `
    <div class="history-item ${item.result.toLowerCase()}">
      <span class="history-seq">#${item.seq}</span>
      <span class="history-value">${item.value}</span>
      <span class="history-badge">${item.result}</span>
    </div>
  `).join('');
}

function updateProgressUI() {
  const total = parseInt(document.getElementById('insp-total-qty').value) || 0;

  document.getElementById('prog-total').textContent = sessionStats.total;
  document.getElementById('prog-pass').textContent = sessionStats.pass;
  document.getElementById('prog-fail').textContent = sessionStats.fail;

  const ratio = total > 0 ? Math.min(Math.round(sessionStats.total / total * 100), 100) : 0;
  document.getElementById('prog-bar').style.width = ratio + '%';
  document.getElementById('prog-ratio').textContent = `${sessionStats.total} / ${total || '?'}`;
}

async function completeInspection() {
  if (!currentSessionId) return;
  if (!confirm('검사를 완료 처리하시겠습니까?')) return;

  try {
    const data = await apiCall(`/inspections/sessions/${currentSessionId}/complete`, 'PUT');
    if (data.success) {
      document.getElementById('active-session-badge').style.display = 'none';
      document.getElementById('btn-complete').disabled = true;
      showToast('검사가 완료되었습니다.', 'success');
      currentSessionId = null;
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function resetInspection() {
  if (!confirm('검사 화면을 초기화하시겠습니까? (진행 중인 검사 기록은 보존됩니다)')) return;

  document.getElementById('insp-material-code').value = '';
  document.getElementById('insp-model-name').value = '';
  document.getElementById('insp-lot-long').value = '';
  document.getElementById('insp-lot-short').value = '';
  document.getElementById('insp-barcode-size').value = '';
  document.getElementById('insp-total-qty').value = '';
  document.getElementById('insp-inspector').value = currentUser.name;
  document.getElementById('insp-shipment-date').value = new Date().toISOString().slice(0,10);
  document.getElementById('scan-input').value = '';
  document.getElementById('scan-result').classList.add('d-none');
  document.getElementById('scan-history-list').innerHTML = `
    <div class="text-center text-muted py-4">
      <i class="fas fa-barcode fa-2x mb-2 d-block opacity-25"></i>
      <small>스캔 이력이 없습니다</small>
    </div>`;
  document.getElementById('scan-count-badge').textContent = '0';
  document.getElementById('session-progress-card').style.display = 'none';
  document.getElementById('btn-complete').disabled = true;
  document.getElementById('active-session-badge').style.display = 'none';

  sessionStats = { total: 0, pass: 0, fail: 0 };
  scanHistory = [];
  currentSessionId = null;

  stopCamera();
  showToast('초기화 완료', 'success');
}

// ── 카메라 스캐너 ─────────────────────────────────────────────────
async function toggleCamera() {
  if (cameraActive) {
    stopCamera();
  } else {
    startCamera();
  }
}

async function startCamera() {
  const container = document.getElementById('camera-container');
  container.classList.remove('d-none');
  document.getElementById('btn-camera').innerHTML = '<i class="fas fa-camera-slash me-1"></i>카메라 끄기';

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    const video = document.getElementById('camera-preview');
    video.srcObject = stream;
    cameraActive = true;

    // html5-qrcode 또는 간단한 프레임 캡처 스캔
    if (typeof Html5Qrcode !== 'undefined') {
      startQRScanner();
    }
  } catch (e) {
    showToast('카메라 접근 권한이 필요합니다: ' + e.message, 'error');
    stopCamera();
  }
}

function startQRScanner() {
  const html5QrCode = new Html5Qrcode("camera-preview");
  cameraScanner = html5QrCode;
  html5QrCode.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: { width: 250, height: 150 } },
    (decodedText) => {
      document.getElementById('scan-input').value = decodedText;
      processScan();
    },
    (error) => {}
  ).catch(e => console.warn(e));
}

function stopCamera() {
  cameraActive = false;
  document.getElementById('camera-container').classList.add('d-none');
  document.getElementById('btn-camera').innerHTML = '<i class="fas fa-camera me-1"></i>카메라';

  const video = document.getElementById('camera-preview');
  if (video.srcObject) {
    video.srcObject.getTracks().forEach(t => t.stop());
    video.srcObject = null;
  }
  if (cameraScanner) {
    cameraScanner.stop().catch(() => {});
    cameraScanner = null;
  }
}

// ── 등록된 제품 불러오기 ──────────────────────────────────────────
function showLoadProduct() {
  const modal = new bootstrap.Modal(document.getElementById('modal-load-product'));
  modal.show();
  searchProductsForLoad();
}

async function searchProductsForLoad() {
  const search = document.getElementById('load-prod-search').value.trim();
  try {
    const data = await apiCall('/products', 'GET', null, search ? { search } : {});
    const tbody = document.getElementById('load-products-tbody');
    if (!data.success || !data.data.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">결과 없음</td></tr>';
      return;
    }
    tbody.innerHTML = data.data.map(p => `
      <tr>
        <td class="font-mono">${p.material_code}</td>
        <td>${p.model_name}</td>
        <td class="font-mono">${p.lot_no}</td>
        <td>${p.quantity || 0} ${p.unit || ''}</td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="loadProductToInspection(${p.id})">
            <i class="fas fa-check me-1"></i>선택
          </button>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function loadProductToInspection(id) {
  try {
    const data = await apiCall(`/products/${id}`);
    const p = data.data;
    document.getElementById('insp-material-code').value = p.material_code || '';
    document.getElementById('insp-model-name').value = p.model_name || '';
    document.getElementById('insp-lot-long').value = p.barcode_long || p.lot_no || '';
    document.getElementById('insp-lot-short').value = p.barcode_short || '';
    document.getElementById('insp-barcode-size').value = p.barcode_size || '';
    document.getElementById('insp-total-qty').value = p.quantity || '';
    if (p.shipment_date) document.getElementById('insp-shipment-date').value = p.shipment_date;

    bootstrap.Modal.getInstance(document.getElementById('modal-load-product')).hide();
    showToast('제품 정보가 불러와졌습니다.', 'success');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// ══════════════════════════════════════════════════════════════════
// 제품 등록
// ══════════════════════════════════════════════════════════════════

async function loadProducts() {
  const search = document.getElementById('prod-search').value.trim();
  const material_code = document.getElementById('prod-filter-code').value.trim();
  const lot_no = document.getElementById('prod-filter-lot').value.trim();
  const model_name = document.getElementById('prod-filter-model').value.trim();

  try {
    const params = {};
    if (search) params.search = search;
    if (material_code) params.material_code = material_code;
    if (lot_no) params.lot_no = lot_no;
    if (model_name) params.model_name = model_name;

    const data = await apiCall('/products', 'GET', null, params);
    const tbody = document.getElementById('products-tbody');

    if (!data.success || !data.data.length) {
      tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-4">등록된 제품이 없습니다</td></tr>';
      return;
    }

    const canEdit = ['admin', 'manager', 'inspector'].includes(currentUser.role);
    tbody.innerHTML = data.data.map((p, i) => `
      <tr>
        <td>${i + 1}</td>
        <td class="font-mono fw-semibold">${p.material_code}</td>
        <td>${p.model_name}</td>
        <td class="font-mono">${p.lot_no}</td>
        <td class="font-mono small">${p.barcode_short || '-'}</td>
        <td>${p.maker || '-'}</td>
        <td>${p.quantity || 0} ${p.unit || ''}</td>
        <td>${p.shipment_date || '-'}</td>
        <td>${p.registered_by_name || '-'}</td>
        <td>
          <div class="btn-group btn-group-sm">
            ${canEdit ? `
              <button class="btn btn-outline-primary" onclick="editProduct(${p.id})" title="수정">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn btn-outline-success" onclick="loadProductToInspection(${p.id}); navigateTo('inspection')" title="검사에 사용">
                <i class="fas fa-search"></i>
              </button>
            ` : ''}
            ${['admin', 'manager'].includes(currentUser.role) ? `
              <button class="btn btn-outline-danger" onclick="deleteProduct(${p.id})" title="삭제">
                <i class="fas fa-trash"></i>
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function showProductModal(product = null) {
  const modal = new bootstrap.Modal(document.getElementById('modal-product'));
  document.getElementById('product-modal-title').textContent = product ? '제품 수정' : '제품 등록';
  document.getElementById('product-id').value = product?.id || '';

  const fields = ['material-code', 'model-name', 'lot-no', 'barcode-long', 'barcode-short',
    'barcode-size', 'maker', 'quantity', 'manufacture-date', 'expiry-date', 'shipment-date', 'notes'];

  if (product) {
    document.getElementById('p-material-code').value = product.material_code || '';
    document.getElementById('p-model-name').value = product.model_name || '';
    document.getElementById('p-lot-no').value = product.lot_no || '';
    document.getElementById('p-barcode-long').value = product.barcode_long || '';
    document.getElementById('p-barcode-short').value = product.barcode_short || '';
    document.getElementById('p-barcode-size').value = product.barcode_size || '';
    document.getElementById('p-maker').value = product.maker || '';
    document.getElementById('p-quantity').value = product.quantity || '';
    document.getElementById('p-unit').value = product.unit || 'Roll';
    document.getElementById('p-manufacture-date').value = product.manufacture_date || '';
    document.getElementById('p-expiry-date').value = product.expiry_date || '';
    document.getElementById('p-shipment-date').value = product.shipment_date || '';
    document.getElementById('p-notes').value = product.notes || '';
  } else {
    ['p-material-code','p-model-name','p-lot-no','p-barcode-long','p-barcode-short',
     'p-barcode-size','p-maker','p-notes'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('p-quantity').value = '';
    document.getElementById('p-unit').value = 'Roll';
    ['p-manufacture-date','p-expiry-date','p-shipment-date'].forEach(id => document.getElementById(id).value = '');
  }

  modal.show();
}

async function editProduct(id) {
  try {
    const data = await apiCall(`/products/${id}`);
    if (data.success) showProductModal(data.data);
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function saveProduct() {
  const id = document.getElementById('product-id').value;
  const payload = {
    material_code: document.getElementById('p-material-code').value.trim(),
    model_name: document.getElementById('p-model-name').value.trim(),
    lot_no: document.getElementById('p-lot-no').value.trim(),
    barcode_long: document.getElementById('p-barcode-long').value.trim(),
    barcode_short: document.getElementById('p-barcode-short').value.trim(),
    barcode_size: document.getElementById('p-barcode-size').value.trim(),
    maker: document.getElementById('p-maker').value.trim(),
    quantity: document.getElementById('p-quantity').value,
    unit: document.getElementById('p-unit').value,
    manufacture_date: document.getElementById('p-manufacture-date').value,
    expiry_date: document.getElementById('p-expiry-date').value,
    shipment_date: document.getElementById('p-shipment-date').value,
    notes: document.getElementById('p-notes').value.trim()
  };

  if (!payload.material_code || !payload.model_name || !payload.lot_no) {
    showToast('자재코드, 모델명, LOT NO는 필수입니다.', 'error');
    return;
  }

  try {
    const data = id
      ? await apiCall(`/products/${id}`, 'PUT', payload)
      : await apiCall('/products', 'POST', payload);

    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById('modal-product')).hide();
      showToast(data.message, 'success');
      loadProducts();
    } else {
      showToast(data.message, 'error');
    }
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function deleteProduct(id) {
  if (!confirm('제품을 삭제하시겠습니까?')) return;
  try {
    const data = await apiCall(`/products/${id}`, 'DELETE');
    if (data.success) { showToast('삭제되었습니다.', 'success'); loadProducts(); }
    else showToast(data.message, 'error');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// ══════════════════════════════════════════════════════════════════
// 검사 기록
// ══════════════════════════════════════════════════════════════════

async function loadRecords(page = 1) {
  recordsCurrentPage = page;
  const params = {
    page,
    limit: 50,
    lot_no: document.getElementById('rec-lot').value.trim(),
    material_code: document.getElementById('rec-code').value.trim(),
    model_name: document.getElementById('rec-model').value.trim(),
    result: document.getElementById('rec-result').value,
    from_date: document.getElementById('rec-from').value,
    to_date: document.getElementById('rec-to').value,
    inspector_name: document.getElementById('rec-inspector').value.trim()
  };

  try {
    const data = await apiCall('/inspections/records', 'GET', null, params);
    const tbody = document.getElementById('records-tbody');

    if (!data.success || !data.data.length) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted py-4">검사 기록이 없습니다</td></tr>';
      document.getElementById('records-info').textContent = '';
      document.getElementById('records-pagination').innerHTML = '';
      renderRecordsSummary(0, 0, 0);
      return;
    }

    // 요약 통계
    const passCount = data.data.filter(r => r.result === 'PASS').length;
    const failCount = data.data.filter(r => r.result === 'FAIL').length;
    renderRecordsSummary(data.total, passCount, failCount);

    const canDelete = ['admin', 'manager'].includes(currentUser.role);
    tbody.innerHTML = data.data.map(r => `
      <tr>
        <td class="fw-bold">${r.sequence_no || '-'}</td>
        <td>${r.inspection_date || '-'}<br><small class="text-muted">${r.inspection_time || ''}</small></td>
        <td>${r.inspector_name || '-'}</td>
        <td class="font-mono">${r.production_lot_no || '-'}</td>
        <td class="font-mono">${r.material_code || '-'}</td>
        <td class="small">${r.model_name || '-'}</td>
        <td>${r.shipment_date || '-'}</td>
        <td class="font-mono small">${r.scanned_value || '-'}</td>
        <td class="font-mono small">${r.expected_value || '-'}</td>
        <td>
          <span class="${r.result === 'PASS' ? 'badge-pass' : 'badge-fail'}">${r.result}</span>
        </td>
        <td>
          ${canDelete ? `
            <button class="btn btn-outline-danger btn-sm" onclick="deleteRecord(${r.id})">
              <i class="fas fa-trash"></i>
            </button>
          ` : '-'}
        </td>
      </tr>
    `).join('');

    // 페이지 정보
    const totalPages = Math.ceil(data.total / data.limit);
    document.getElementById('records-info').textContent =
      `전체 ${data.total}건 (${page}/${totalPages} 페이지)`;

    renderPagination(page, totalPages);
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function renderRecordsSummary(total, pass, fail) {
  const rate = total > 0 ? Math.round(pass / total * 100) : 0;
  document.getElementById('records-summary').innerHTML = `
    <div class="col-4 col-md-2">
      <div class="card irms-card text-center p-2">
        <div class="fw-bold text-primary fs-5">${total}</div>
        <small class="text-muted">총 기록</small>
      </div>
    </div>
    <div class="col-4 col-md-2">
      <div class="card irms-card text-center p-2" style="background:#d1fae5">
        <div class="fw-bold text-success fs-5">${pass}</div>
        <small class="text-muted">PASS</small>
      </div>
    </div>
    <div class="col-4 col-md-2">
      <div class="card irms-card text-center p-2" style="background:#fee2e2">
        <div class="fw-bold text-danger fs-5">${fail}</div>
        <small class="text-muted">FAIL</small>
      </div>
    </div>
    <div class="col-12 col-md-2">
      <div class="card irms-card text-center p-2">
        <div class="fw-bold fs-5" style="color:${rate >= 90 ? '#057a55' : rate >= 70 ? '#d97706' : '#c81e1e'}">${rate}%</div>
        <small class="text-muted">합격률</small>
      </div>
    </div>
  `;
}

function renderPagination(current, total) {
  const ul = document.getElementById('records-pagination');
  if (total <= 1) { ul.innerHTML = ''; return; }

  let html = `
    <li class="page-item ${current === 1 ? 'disabled' : ''}">
      <a class="page-link" href="#" onclick="loadRecords(${current - 1})">이전</a>
    </li>
  `;

  const start = Math.max(1, current - 2);
  const end = Math.min(total, current + 2);

  for (let i = start; i <= end; i++) {
    html += `
      <li class="page-item ${i === current ? 'active' : ''}">
        <a class="page-link" href="#" onclick="loadRecords(${i})">${i}</a>
      </li>
    `;
  }

  html += `
    <li class="page-item ${current === total ? 'disabled' : ''}">
      <a class="page-link" href="#" onclick="loadRecords(${current + 1})">다음</a>
    </li>
  `;

  ul.innerHTML = html;
}

function resetRecordSearch() {
  ['rec-lot','rec-code','rec-model','rec-inspector'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('rec-result').value = '';
  document.getElementById('rec-from').value = '';
  document.getElementById('rec-to').value = '';
  loadRecords();
}

async function deleteRecord(id) {
  if (!confirm('이 기록을 삭제하시겠습니까?')) return;
  try {
    const data = await apiCall(`/inspections/records/${id}`, 'DELETE');
    if (data.success) { showToast('삭제되었습니다.', 'success'); loadRecords(recordsCurrentPage); }
    else showToast(data.message, 'error');
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Excel 내보내기 ────────────────────────────────────────────────
function exportRecords() {
  const params = new URLSearchParams({
    lot_no: document.getElementById('rec-lot')?.value || '',
    material_code: document.getElementById('rec-code')?.value || '',
    from_date: document.getElementById('rec-from')?.value || '',
    to_date: document.getElementById('rec-to')?.value || '',
    result: document.getElementById('rec-result')?.value || ''
  });

  const url = `/api/export/records?${params}&token=${authToken}`;
  // Authorization 헤더를 URL로 처리하기 위해 임시 링크 생성
  const link = document.createElement('a');
  link.href = `/api/export/records?${params}`;
  link.setAttribute('download', '');

  fetch(link.href, { headers: { 'Authorization': `Bearer ${authToken}` } })
    .then(res => {
      if (!res.ok) throw new Error('내보내기 실패');
      return res.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `검사기록_${new Date().toISOString().slice(0,10)}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Excel 파일 다운로드 완료', 'success');
    })
    .catch(e => showToast(e.message, 'error'));
}

// ══════════════════════════════════════════════════════════════════
// 사용자 관리
// ══════════════════════════════════════════════════════════════════

async function loadUsers() {
  try {
    const data = await apiCall('/users');
    const tbody = document.getElementById('users-tbody');
    const roleLabels = { admin: '관리자', manager: '담당자', inspector: '검사원', viewer: '조회자' };

    if (!data.success || !data.data.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">사용자가 없습니다</td></tr>';
      return;
    }

    tbody.innerHTML = data.data.map((u, i) => `
      <tr>
        <td>${i + 1}</td>
        <td class="fw-semibold">${u.username}</td>
        <td>${u.name}</td>
        <td><span class="role-${u.role}">${roleLabels[u.role] || u.role}</span></td>
        <td>${u.department || '-'}</td>
        <td>${u.email || '-'}</td>
        <td>
          <span class="badge ${u.active ? 'bg-success' : 'bg-secondary'}">
            ${u.active ? '활성' : '비활성'}
          </span>
        </td>
        <td class="small">${u.last_login ? u.last_login.slice(0,16) : '-'}</td>
        <td>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" onclick="editUser(${u.id})"><i class="fas fa-edit"></i></button>
            ${u.id !== currentUser.id ? `
              <button class="btn btn-outline-danger" onclick="deactivateUser(${u.id})"><i class="fas fa-user-slash"></i></button>
            ` : ''}
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function showUserModal(user = null) {
  document.getElementById('user-modal-title').textContent = user ? '사용자 수정' : '사용자 추가';
  document.getElementById('user-id').value = user?.id || '';
  document.getElementById('u-username').value = user?.username || '';
  document.getElementById('u-username').disabled = false;
  document.getElementById('u-password').value = '';
  document.getElementById('u-pwd-required').textContent = user ? '(변경 시 입력)' : '*';
  document.getElementById('u-name').value = user?.name || '';
  document.getElementById('u-role').value = user?.role || 'inspector';
  document.getElementById('u-department').value = user?.department || '';
  document.getElementById('u-email').value = user?.email || '';
  document.getElementById('u-active').value = user?.active !== undefined ? user.active : 1;

  new bootstrap.Modal(document.getElementById('modal-user')).show();
}

async function editUser(id) {
  try {
    const data = await apiCall('/users');
    const user = data.data.find(u => u.id === id);
    if (user) showUserModal(user);
  } catch (e) { showToast(e.message, 'error'); }
}

async function saveUser() {
  const id = document.getElementById('user-id').value;
  const payload = {
    username: document.getElementById('u-username').value.trim(),
    password: document.getElementById('u-password').value,
    name: document.getElementById('u-name').value.trim(),
    role: document.getElementById('u-role').value,
    department: document.getElementById('u-department').value.trim(),
    email: document.getElementById('u-email').value.trim(),
    active: document.getElementById('u-active').value
  };
  if (!payload.username) { showToast('아이디를 입력하세요.', 'error'); return; }
  if (!payload.name) { showToast('이름을 입력하세요.', 'error'); return; }
  if (!id && !payload.password) { showToast('비밀번호를 입력하세요.', 'error'); return; }
  if (!payload.password) delete payload.password;

  try {
    const data = id
      ? await apiCall(`/users/${id}`, 'PUT', payload)
      : await apiCall('/users', 'POST', payload);

    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById('modal-user')).hide();
      showToast(data.message, 'success');
      loadUsers();
    } else {
      showToast(data.message, 'error');
    }
  } catch (e) { showToast(e.message, 'error'); }
}

async function deactivateUser(id) {
  if (!confirm('이 사용자를 비활성화하시겠습니까?')) return;
  try {
    const data = await apiCall(`/users/${id}`, 'DELETE');
    if (data.success) { showToast(data.message, 'success'); loadUsers(); }
    else showToast(data.message, 'error');
  } catch (e) { showToast(e.message, 'error'); }
}

// ── 비밀번호 변경 ─────────────────────────────────────────────────
function showChangePassword() {
  document.getElementById('pwd-current').value = '';
  document.getElementById('pwd-new').value = '';
  document.getElementById('pwd-confirm').value = '';
  new bootstrap.Modal(document.getElementById('modal-change-pwd')).show();
}

async function changePassword() {
  const current = document.getElementById('pwd-current').value;
  const newPwd = document.getElementById('pwd-new').value;
  const confirm = document.getElementById('pwd-confirm').value;

  if (!current || !newPwd) { showToast('모든 항목을 입력하세요.', 'error'); return; }
  if (newPwd !== confirm) { showToast('새 비밀번호가 일치하지 않습니다.', 'error'); return; }
  if (newPwd.length < 6) { showToast('비밀번호는 6자 이상이어야 합니다.', 'error'); return; }

  try {
    const data = await apiCall('/auth/change-password', 'POST', {
      current_password: current,
      new_password: newPwd
    });
    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById('modal-change-pwd')).hide();
      showToast(data.message, 'success');
    } else {
      showToast(data.message, 'error');
    }
  } catch (e) { showToast(e.message, 'error'); }
}

// ══════════════════════════════════════════════════════════════════
// 시스템 설정
// ══════════════════════════════════════════════════════════════════

let settingsData = [];

async function loadSettings() {
  try {
    const data = await apiCall('/users/settings/all');
    if (!data.success) return showToast(data.message, 'error');
    settingsData = data.data || [];

    // 카드 UI 값 채우기
    const get = (key) => (settingsData.find(s => s.key === key) || {}).value || '';
    document.getElementById('cfg-company-name').value = get('company_name');
    document.getElementById('cfg-system-version').value = get('system_version');
    document.getElementById('cfg-barcode-type-1').value = get('barcode_type_1') || 'material_code';
    document.getElementById('cfg-barcode-type-2').value = get('barcode_type_2') || 'lot_no_long';
    document.getElementById('cfg-barcode-type-3').value = get('barcode_type_3') || 'lot_no_short';
    document.getElementById('cfg-auto-sequence').value = get('auto_sequence') || 'true';

    // 전체 목록 테이블
    const tbody = document.getElementById('settings-tbody');
    tbody.innerHTML = settingsData.map(s => `
      <tr>
        <td class="fw-semibold font-mono small">${s.key}</td>
        <td>
          <input type="text" class="form-control form-control-sm" value="${s.value || ''}"
            onchange="updateSettingValue('${s.key}', this.value)" style="min-width:120px">
        </td>
        <td class="small text-muted">${s.description || '-'}</td>
        <td class="small">${s.updated_at ? s.updated_at.slice(0,16) : '-'}</td>
        <td>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteSetting('${s.key}')">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// 카드 UI에서 일괄 저장
async function saveAllSettings() {
  const updates = [
    { key: 'company_name', value: document.getElementById('cfg-company-name').value.trim() },
    { key: 'system_version', value: document.getElementById('cfg-system-version').value.trim() },
    { key: 'barcode_type_1', value: document.getElementById('cfg-barcode-type-1').value },
    { key: 'barcode_type_2', value: document.getElementById('cfg-barcode-type-2').value },
    { key: 'barcode_type_3', value: document.getElementById('cfg-barcode-type-3').value },
    { key: 'auto_sequence', value: document.getElementById('cfg-auto-sequence').value },
  ];
  try {
    for (const u of updates) {
      await apiCall('/users/settings/update', 'PUT', u);
    }
    showToast('설정이 저장되었습니다.', 'success');
    loadSettings();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// 테이블에서 개별 값 변경 (즉시 저장)
async function updateSettingValue(key, value) {
  try {
    const data = await apiCall('/users/settings/update', 'PUT', { key, value });
    if (data.success) showToast(`'${key}' 저장됨`, 'success');
    else showToast(data.message, 'error');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function showAddSettingModal() {
  document.getElementById('new-setting-key').value = '';
  document.getElementById('new-setting-value').value = '';
  document.getElementById('new-setting-desc').value = '';
  new bootstrap.Modal(document.getElementById('modal-add-setting')).show();
}

async function addNewSetting() {
  const key = document.getElementById('new-setting-key').value.trim();
  const value = document.getElementById('new-setting-value').value.trim();
  const description = document.getElementById('new-setting-desc').value.trim();
  if (!key || !value) { showToast('키와 값을 입력하세요.', 'error'); return; }
  try {
    const data = await apiCall('/users/settings/add', 'POST', { key, value, description });
    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById('modal-add-setting')).hide();
      showToast(data.message, 'success');
      loadSettings();
    } else {
      showToast(data.message, 'error');
    }
  } catch (e) { showToast(e.message, 'error'); }
}

async function deleteSetting(key) {
  if (!confirm(`'${key}' 설정을 삭제하시겠습니까?`)) return;
  try {
    const data = await apiCall(`/users/settings/${encodeURIComponent(key)}`, 'DELETE');
    if (data.success) { showToast(data.message, 'success'); loadSettings(); }
    else showToast(data.message, 'error');
  } catch (e) { showToast(e.message, 'error'); }
}
