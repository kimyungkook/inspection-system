const express = require('express');
const router = express.Router();
const { getDb } = require('../database');
const { authenticateToken } = require('../middleware/auth');

router.use(authenticateToken);

// GET /api/products - 전체 제품 목록
router.get('/', (req, res) => {
  const db = getDb();
  const { search, material_code, lot_no, model_name } = req.query;
  let sql = `
    SELECT p.*, u.name as registered_by_name
    FROM products p
    LEFT JOIN users u ON p.registered_by = u.id
    WHERE 1=1
  `;
  const params = [];

  if (search) {
    sql += ` AND (p.material_code LIKE ? OR p.lot_no LIKE ? OR p.model_name LIKE ? OR p.barcode_short LIKE ? OR p.barcode_long LIKE ?)`;
    const s = `%${search}%`;
    params.push(s, s, s, s, s);
  }
  if (material_code) { sql += ` AND p.material_code LIKE ?`; params.push(`%${material_code}%`); }
  if (lot_no) { sql += ` AND p.lot_no LIKE ?`; params.push(`%${lot_no}%`); }
  if (model_name) { sql += ` AND p.model_name LIKE ?`; params.push(`%${model_name}%`); }

  sql += ` ORDER BY p.created_at DESC`;

  db.all(sql, params, (err, rows) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, data: rows });
  });
});

// GET /api/products/:id
router.get('/:id', (req, res) => {
  const db = getDb();
  db.get(`SELECT p.*, u.name as registered_by_name FROM products p LEFT JOIN users u ON p.registered_by = u.id WHERE p.id = ?`,
    [req.params.id], (err, row) => {
      if (err) return res.status(500).json({ success: false, message: err.message });
      if (!row) return res.status(404).json({ success: false, message: '제품을 찾을 수 없습니다.' });
      res.json({ success: true, data: row });
    });
});

// POST /api/products - 제품 등록
router.post('/', (req, res) => {
  const { material_code, model_name, lot_no, barcode_short, barcode_long, barcode_size,
    maker, quantity, unit, manufacture_date, expiry_date, shipment_date, notes } = req.body;

  if (!material_code || !model_name || !lot_no) {
    return res.status(400).json({ success: false, message: '자재코드, 모델명, LOT NO는 필수입니다.' });
  }

  const db = getDb();
  db.run(`
    INSERT INTO products (material_code, model_name, lot_no, barcode_short, barcode_long, barcode_size,
      maker, quantity, unit, manufacture_date, expiry_date, shipment_date, notes, registered_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [material_code, model_name, lot_no, barcode_short, barcode_long, barcode_size,
    maker, quantity, unit || 'Roll', manufacture_date, expiry_date, shipment_date, notes, req.user.id],
    function (err) {
      if (err) return res.status(500).json({ success: false, message: err.message });
      db.run(`INSERT INTO audit_logs (user_id, username, action, target_table, target_id, detail) VALUES (?, ?, 'CREATE', 'products', ?, ?)`,
        [req.user.id, req.user.username, this.lastID, `제품 등록: ${material_code} / ${lot_no}`]);
      res.json({ success: true, message: '제품이 등록되었습니다.', id: this.lastID });
    });
});

// PUT /api/products/:id
router.put('/:id', (req, res) => {
  const { material_code, model_name, lot_no, barcode_short, barcode_long, barcode_size,
    maker, quantity, unit, manufacture_date, expiry_date, shipment_date, notes } = req.body;
  const db = getDb();
  db.run(`
    UPDATE products SET material_code=?, model_name=?, lot_no=?, barcode_short=?, barcode_long=?,
    barcode_size=?, maker=?, quantity=?, unit=?, manufacture_date=?, expiry_date=?,
    shipment_date=?, notes=? WHERE id=?
  `, [material_code, model_name, lot_no, barcode_short, barcode_long, barcode_size,
    maker, quantity, unit, manufacture_date, expiry_date, shipment_date, notes, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ success: false, message: err.message });
      db.run(`INSERT INTO audit_logs (user_id, username, action, target_table, target_id, detail) VALUES (?, ?, 'UPDATE', 'products', ?, ?)`,
        [req.user.id, req.user.username, req.params.id, `제품 수정: ${material_code}`]);
      res.json({ success: true, message: '제품 정보가 수정되었습니다.' });
    });
});

// DELETE /api/products/:id
router.delete('/:id', require('../middleware/auth').requireRole('admin', 'manager'), (req, res) => {
  const db = getDb();
  db.run('DELETE FROM products WHERE id = ?', [req.params.id], (err) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, message: '제품이 삭제되었습니다.' });
  });
});

module.exports = router;
