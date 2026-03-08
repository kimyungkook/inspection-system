const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const { getDb } = require('../database');
const { authenticateToken, requireRole } = require('../middleware/auth');

router.use(authenticateToken);

// GET /api/users
router.get('/', requireRole('admin', 'manager'), (req, res) => {
  const db = getDb();
  db.all(`SELECT id, username, name, role, department, email, active, created_at, last_login FROM users ORDER BY id`, [], (err, rows) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, data: rows });
  });
});

// GET /api/users/me
router.get('/me', (req, res) => {
  const db = getDb();
  db.get('SELECT id, username, name, role, department, email, active FROM users WHERE id = ?', [req.user.id], (err, row) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, data: row });
  });
});

// POST /api/users
router.post('/', requireRole('admin'), (req, res) => {
  const { username, password, name, role, department, email } = req.body;
  if (!username || !password || !name) {
    return res.status(400).json({ success: false, message: '아이디, 비밀번호, 이름은 필수입니다.' });
  }
  const hash = bcrypt.hashSync(password, 10);
  const db = getDb();
  db.run(`INSERT INTO users (username, password, name, role, department, email) VALUES (?, ?, ?, ?, ?, ?)`,
    [username, hash, name, role || 'inspector', department, email],
    function (err) {
      if (err) {
        if (err.message.includes('UNIQUE')) return res.status(400).json({ success: false, message: '이미 사용중인 아이디입니다.' });
        return res.status(500).json({ success: false, message: err.message });
      }
      res.json({ success: true, message: '사용자가 등록되었습니다.', id: this.lastID });
    });
});

// PUT /api/users/:id
router.put('/:id', requireRole('admin'), (req, res) => {
  const { name, role, department, email, active, password } = req.body;
  const db = getDb();

  if (password) {
    const hash = bcrypt.hashSync(password, 10);
    db.run(`UPDATE users SET name=?, role=?, department=?, email=?, active=?, password=? WHERE id=?`,
      [name, role, department, email, active, hash, req.params.id], (err) => {
        if (err) return res.status(500).json({ success: false, message: err.message });
        res.json({ success: true, message: '사용자 정보가 수정되었습니다.' });
      });
  } else {
    db.run(`UPDATE users SET name=?, role=?, department=?, email=?, active=? WHERE id=?`,
      [name, role, department, email, active, req.params.id], (err) => {
        if (err) return res.status(500).json({ success: false, message: err.message });
        res.json({ success: true, message: '사용자 정보가 수정되었습니다.' });
      });
  }
});

// DELETE /api/users/:id
router.delete('/:id', requireRole('admin'), (req, res) => {
  if (parseInt(req.params.id) === req.user.id) {
    return res.status(400).json({ success: false, message: '자기 자신은 삭제할 수 없습니다.' });
  }
  const db = getDb();
  db.run('UPDATE users SET active = 0 WHERE id = ?', [req.params.id], (err) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, message: '사용자가 비활성화되었습니다.' });
  });
});

// GET /api/users/settings
router.get('/settings/all', requireRole('admin'), (req, res) => {
  const db = getDb();
  db.all('SELECT * FROM system_settings', [], (err, rows) => {
    if (err) return res.status(500).json({ success: false, message: err.message });
    res.json({ success: true, data: rows });
  });
});

// PUT /api/users/settings
router.put('/settings/update', requireRole('admin'), (req, res) => {
  const { key, value } = req.body;
  const db = getDb();
  db.run(`UPDATE system_settings SET value=?, updated_by=?, updated_at=datetime('now','localtime') WHERE key=?`,
    [value, req.user.id, key], (err) => {
      if (err) return res.status(500).json({ success: false, message: err.message });
      res.json({ success: true, message: '설정이 저장되었습니다.' });
    });
});

module.exports = router;
