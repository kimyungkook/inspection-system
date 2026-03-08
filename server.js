const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
const bodyParser = require('body-parser');
const { initDatabase } = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;

// ─── 글로벌 에러 핸들러 (서버 크래시 방지) ────────────────────────
process.on('uncaughtException', (err) => {
  console.error('❌ 예상치 못한 오류:', err.message);
  console.error(err.stack);
});
process.on('unhandledRejection', (reason) => {
  console.error('❌ 처리되지 않은 Promise 거부:', reason);
});

// ─── 미들웨어 ──────────────────────────────────────────────────────
app.use(cors({ origin: '*', methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'] }));
app.options('*', cors());
app.use(morgan('dev'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// ─── 정적 파일 ─────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname, 'public')));

// ─── API 라우트 ────────────────────────────────────────────────────
app.use('/api/auth', require('./routes/auth'));
app.use('/api/products', require('./routes/products'));
app.use('/api/inspections', require('./routes/inspections'));
app.use('/api/users', require('./routes/users'));

// ─── 내보내기 API (Excel) ──────────────────────────────────────────
const { authenticateToken } = require('./middleware/auth');
const { getDb } = require('./database');
const XLSX = require('xlsx');

app.get('/api/export/records', authenticateToken, (req, res) => {
  const db = getDb();
  const { lot_no, material_code, from_date, to_date, result } = req.query;
  let sql = `SELECT r.sequence_no as '순번', r.inspection_date as '검사일자', r.inspection_time as '검사시간',
    r.inspector_name as '검사자', r.production_lot_no as '생산LOT NO', r.material_code as '자재코드',
    r.model_name as '모델명', r.shipment_date as '출하일자', r.scanned_value as '스캔값',
    r.expected_value as '등록값', r.result as '검사결과', r.fail_reason as '불합격사유'
    FROM inspection_records r WHERE 1=1`;
  const params = [];
  if (lot_no) { sql += ` AND r.production_lot_no LIKE ?`; params.push(`%${lot_no}%`); }
  if (material_code) { sql += ` AND r.material_code LIKE ?`; params.push(`%${material_code}%`); }
  if (from_date) { sql += ` AND r.inspection_date >= ?`; params.push(from_date); }
  if (to_date) { sql += ` AND r.inspection_date <= ?`; params.push(to_date); }
  if (result) { sql += ` AND r.result = ?`; params.push(result); }
  sql += ` ORDER BY r.created_at DESC`;

  db.all(sql, params, (err, rows) => {
    if (err) return res.status(500).json({ success: false, message: err.message });

    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();

    // 컬럼 너비 설정
    ws['!cols'] = [
      { wch: 6 }, { wch: 12 }, { wch: 10 }, { wch: 12 }, { wch: 16 },
      { wch: 14 }, { wch: 30 }, { wch: 12 }, { wch: 20 }, { wch: 20 },
      { wch: 10 }, { wch: 40 }
    ];

    XLSX.utils.book_append_sheet(wb, ws, '검사기록');

    const buf = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
    const filename = `검사기록_${new Date().toISOString().slice(0,10)}.xlsx`;

    res.setHeader('Content-Disposition', `attachment; filename*=UTF-8''${encodeURIComponent(filename)}`);
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.send(buf);
  });
});

// ─── SPA 폴백 ──────────────────────────────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ─── 오류 핸들러 ───────────────────────────────────────────────────
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ success: false, message: '서버 오류가 발생했습니다.' });
});

// ─── 서버 시작 ─────────────────────────────────────────────────────
initDatabase();
app.listen(PORT, '0.0.0.0', () => {
  console.log(`
╔══════════════════════════════════════════════════════════╗
║        검사기록관리 시스템 v01  -  서버 시작됨            ║
╠══════════════════════════════════════════════════════════╣
║  로컬 접속:  http://localhost:${PORT}                      ║
║  네트워크:   http://[IP주소]:${PORT}                       ║
╠══════════════════════════════════════════════════════════╣
║  기본 계정:  admin / admin1234  (관리자)                   ║
║             inspector01 / inspector1234 (검사원)           ║
╚══════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;
