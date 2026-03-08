const express = require('express');
const router = express.Router();
const { getDb } = require('../database');
const { authenticateToken } = require('../middleware/auth');

router.use(authenticateToken);

// ════════════════════════════════════════════════════════════════════
// 검사 세션
// ════════════════════════════════════════════════════════════════════

// POST /api/inspections/sessions - 새 검사 세션 시작
router.post('/sessions', (req, res) => {
  const { product_id, material_code, model_name, lot_no, shipment_date, total_quantity, notes } = req.body;
  const db = getDb();

  const now = new Date();
  const code = `S${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}-${String(now.getTime()).slice(-5)}`;

  db.run(`
    INSERT INTO inspection_sessions (session_code, product_id, material_code, model_name, lot_no,
      shipment_date, total_quantity, inspector_id, inspector_name, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [code, product_id || null, material_code, model_name, lot_no, shipment_date,
    total_quantity || 0, req.user.id, req.user.name, notes],
    function (err) {
      if (err) return res.status(500).json({ success: false, message: err.message });
      res.json({ success: true, session_id: this.lastID, session_code: code });
    });
});

// GET /api/inspections/sessions - 세션 목록
router.get('/sessions', (req, res) => {
  const db = getDb();
  const { status, lot_no, material_code, from_date, to_date } = req.query;
  let sql = `SELECT * FROM inspection_sessions WHERE 1=1`;
  const params = [];
  if (status) { sql += ` AND status = ?`; params.push(status); }
  if (lot_no) { sql += ` AND lot_no LIKE ?`; params.push(`%${lot_no}%`); }
  if (material_code) { sql += ` AND material_code LIKE ?`; params.push(`%${material_code}%`); }
  if (from_date) { sql += ` AND date(started_at) >= ?`; params.push(from_date); }
  if (to_date) { sql += ` AND date(started_at) <= ?`; params.push(to_date); }
  sql += ` ORDER BY started_at DESC`;
  db.all(sql, params, (err, rows) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, data: rows });
  });
});

// GET /api/inspections/sessions/:id
router.get('/sessions/:id', (req, res) => {
  const db = getDb();
  db.get('SELECT * FROM inspection_sessions WHERE id = ?', [req.params.id], (err, session) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    if (!session) return res.status(404).json({ success: false, message: '세션을 찾을 수 없습니다.' });
    db.all('SELECT * FROM inspection_records WHERE session_id = ? ORDER BY sequence_no',
      [req.params.id], (err, records) => {
        if (err) return res.status(500).json({ success: false, message: err.message });
        res.json({ success: true, data: { session, records } });
      });
  });
});

// PUT /api/inspections/sessions/:id/complete
router.put('/sessions/:id/complete', (req, res) => {
  const db = getDb();
  db.run(`UPDATE inspection_sessions SET status='completed', completed_at=datetime('now','localtime') WHERE id=?`,
    [req.params.id], (err) => {
      if (err) return res.status(500).json({ success: false, message: err.message });
      res.json({ success: true, message: '검사가 완료되었습니다.' });
    });
});

// ════════════════════════════════════════════════════════════════════
// 바코드 스캔 및 검사
// ════════════════════════════════════════════════════════════════════

// POST /api/inspections/scan - 바코드 스캔 검사
router.post('/scan', (req, res) => {
  const { session_id, scanned_value, scan_type, expected_value,
    material_code, model_name, lot_no, shipment_date } = req.body;

  if (!scanned_value) {
    return res.status(400).json({ success: false, message: '스캔 값이 없습니다.' });
  }

  const db = getDb();

  // 비교 로직: 공백/대소문자 무시 옵션
  const normalize = (s) => (s || '').trim().toUpperCase().replace(/\s+/g, '');
  const isMatch = normalize(scanned_value) === normalize(expected_value);
  const result = isMatch ? 'PASS' : 'FAIL';
  const fail_reason = !isMatch ? `스캔값(${scanned_value}) ≠ 등록값(${expected_value})` : null;

  // 순번 계산
  db.get('SELECT MAX(sequence_no) as max_seq FROM inspection_records WHERE session_id = ?',
    [session_id || 0], (err, row) => {
      const seq = (row && row.max_seq ? row.max_seq : 0) + 1;

      db.run(`
        INSERT INTO inspection_records
          (sequence_no, session_id, inspector_id, inspector_name, production_lot_no,
           material_code, model_name, shipment_date, scanned_value, expected_value,
           scan_type, result, fail_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `, [seq, session_id || null, req.user.id, req.user.name,
        lot_no, material_code, model_name, shipment_date,
        scanned_value, expected_value, scan_type || 'manual',
        result, fail_reason],
        function (err) {
          if (err) return res.status(500).json({ success: false, message: err.message });

          // 세션 통계 업데이트
          if (session_id) {
            if (result === 'PASS') {
              db.run(`UPDATE inspection_sessions SET inspected_count=inspected_count+1, pass_count=pass_count+1 WHERE id=?`, [session_id]);
            } else {
              db.run(`UPDATE inspection_sessions SET inspected_count=inspected_count+1, fail_count=fail_count+1 WHERE id=?`, [session_id]);
            }
          }

          res.json({
            success: true,
            result,
            sequence_no: seq,
            record_id: this.lastID,
            is_match: isMatch,
            scanned_value,
            expected_value,
            fail_reason
          });
        });
    });
});

// ════════════════════════════════════════════════════════════════════
// 검사 기록 조회
// ════════════════════════════════════════════════════════════════════

// GET /api/inspections/records - 기록 목록 (검색/필터)
router.get('/records', (req, res) => {
  const db = getDb();
  const { lot_no, material_code, model_name, result, from_date, to_date,
    inspector_name, search, page = 1, limit = 50 } = req.query;

  let sql = `SELECT r.*, s.session_code FROM inspection_records r
    LEFT JOIN inspection_sessions s ON r.session_id = s.id WHERE 1=1`;
  const params = [];

  if (lot_no) { sql += ` AND r.production_lot_no LIKE ?`; params.push(`%${lot_no}%`); }
  if (material_code) { sql += ` AND r.material_code LIKE ?`; params.push(`%${material_code}%`); }
  if (model_name) { sql += ` AND r.model_name LIKE ?`; params.push(`%${model_name}%`); }
  if (result) { sql += ` AND r.result = ?`; params.push(result); }
  if (from_date) { sql += ` AND r.inspection_date >= ?`; params.push(from_date); }
  if (to_date) { sql += ` AND r.inspection_date <= ?`; params.push(to_date); }
  if (inspector_name) { sql += ` AND r.inspector_name LIKE ?`; params.push(`%${inspector_name}%`); }
  if (search) {
    sql += ` AND (r.production_lot_no LIKE ? OR r.material_code LIKE ? OR r.model_name LIKE ? OR r.scanned_value LIKE ?)`;
    const s = `%${search}%`; params.push(s, s, s, s);
  }

  // Count total
  db.get(`SELECT COUNT(*) as total FROM (${sql})`, params, (err, countRow) => {
    const total = countRow ? countRow.total : 0;
    sql += ` ORDER BY r.created_at DESC LIMIT ? OFFSET ?`;
    params.push(parseInt(limit), (parseInt(page) - 1) * parseInt(limit));

    db.all(sql, params, (err, rows) => {
      if (err) return res.status(500).json({ success: false, message: err.message });
      res.json({ success: true, data: rows, total, page: parseInt(page), limit: parseInt(limit) });
    });
  });
});

// GET /api/inspections/stats - 통계
router.get('/stats', (req, res) => {
  const db = getDb();
  const today = new Date().toISOString().slice(0, 10);

  db.all(`
    SELECT
      (SELECT COUNT(*) FROM inspection_records WHERE inspection_date = ?) as today_total,
      (SELECT COUNT(*) FROM inspection_records WHERE inspection_date = ? AND result='PASS') as today_pass,
      (SELECT COUNT(*) FROM inspection_records WHERE inspection_date = ? AND result='FAIL') as today_fail,
      (SELECT COUNT(*) FROM inspection_records) as all_total,
      (SELECT COUNT(*) FROM inspection_records WHERE result='PASS') as all_pass,
      (SELECT COUNT(*) FROM inspection_records WHERE result='FAIL') as all_fail,
      (SELECT COUNT(*) FROM inspection_sessions WHERE status='in_progress') as active_sessions,
      (SELECT COUNT(*) FROM products) as total_products
  `, [today, today, today], (err, rows) => {
    if (err) return res.status(500).json({ success: false, message: err.message });

    // 최근 7일 트렌드
    db.all(`
      SELECT inspection_date,
        COUNT(*) as total,
        SUM(CASE WHEN result='PASS' THEN 1 ELSE 0 END) as pass_count,
        SUM(CASE WHEN result='FAIL' THEN 1 ELSE 0 END) as fail_count
      FROM inspection_records
      WHERE inspection_date >= date('now','-6 days','localtime')
      GROUP BY inspection_date ORDER BY inspection_date
    `, [], (err2, trend) => {
      res.json({ success: true, data: rows[0], trend: trend || [] });
    });
  });
});

// DELETE /api/inspections/records/:id
router.delete('/records/:id', require('../middleware/auth').requireRole('admin', 'manager'), (req, res) => {
  const db = getDb();
  db.run('DELETE FROM inspection_records WHERE id = ?', [req.params.id], (err) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, message: '기록이 삭제되었습니다.' });
  });
});

module.exports = router;
