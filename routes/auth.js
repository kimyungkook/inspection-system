const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { getDb } = require('../database');
const { JWT_SECRET } = require('../middleware/auth');

// POST /api/auth/login
router.post('/login', (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ success: false, message: '아이디와 비밀번호를 입력하세요.' });
  }

  const db = getDb();
  db.get('SELECT * FROM users WHERE username = ? AND active = 1', [username], (err, user) => {
    if (err) return res.status(500).json({ success: false, message: 'DB 오류' });
    if (!user) return res.status(401).json({ success: false, message: '아이디 또는 비밀번호가 올바르지 않습니다.' });

    bcrypt.compare(password, user.password, (err, match) => {
      if (!match) return res.status(401).json({ success: false, message: '아이디 또는 비밀번호가 올바르지 않습니다.' });

      const token = jwt.sign(
        { id: user.id, username: user.username, name: user.name, role: user.role, department: user.department },
        JWT_SECRET,
        { expiresIn: '12h' }
      );

      db.run('UPDATE users SET last_login = datetime("now","localtime") WHERE id = ?', [user.id]);

      // Audit log
      const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
      db.run(`INSERT INTO audit_logs (user_id, username, action, detail, ip_address) VALUES (?, ?, 'LOGIN', '로그인 성공', ?)`,
        [user.id, user.username, ip]);

      res.json({
        success: true,
        token,
        user: { id: user.id, username: user.username, name: user.name, role: user.role, department: user.department }
      });
    });
  });
});

// POST /api/auth/logout
router.post('/logout', (req, res) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (token) {
    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      const db = getDb();
      const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
      db.run(`INSERT INTO audit_logs (user_id, username, action, detail, ip_address) VALUES (?, ?, 'LOGOUT', '로그아웃', ?)`,
        [decoded.id, decoded.username, ip]);
    } catch (e) {}
  }
  res.json({ success: true, message: '로그아웃 되었습니다.' });
});

// POST /api/auth/change-password
router.post('/change-password', require('../middleware/auth').authenticateToken, (req, res) => {
  const { current_password, new_password } = req.body;
  const db = getDb();
  db.get('SELECT * FROM users WHERE id = ?', [req.user.id], (err, user) => {
    if (err || !user) return res.status(404).json({ success: false, message: '사용자를 찾을 수 없습니다.' });
    bcrypt.compare(current_password, user.password, (err, match) => {
      if (!match) return res.status(400).json({ success: false, message: '현재 비밀번호가 올바르지 않습니다.' });
      const newHash = bcrypt.hashSync(new_password, 10);
      db.run('UPDATE users SET password = ? WHERE id = ?', [newHash, req.user.id], (err) => {
        if (err) return res.status(500).json({ success: false, message: 'DB 오류' });
        res.json({ success: true, message: '비밀번호가 변경되었습니다.' });
      });
    });
  });
});

module.exports = router;
