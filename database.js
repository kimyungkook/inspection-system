const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bcrypt = require('bcryptjs');

const DB_PATH = path.join(__dirname, 'data', 'inspection.db');

let db;

function getDb() {
  if (!db) {
    db = new sqlite3.Database(DB_PATH, (err) => {
      if (err) console.error('DB 연결 오류:', err);
      else console.log('✅ 데이터베이스 연결됨:', DB_PATH);
    });
    db.run('PRAGMA foreign_keys = ON');
    db.run('PRAGMA journal_mode = WAL');
  }
  return db;
}

function initDatabase() {
  const database = getDb();

  database.serialize(() => {
    // ─── 사용자 테이블 ───────────────────────────────────────────────
    database.run(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'inspector' CHECK(role IN ('admin','manager','inspector','viewer')),
        department TEXT,
        email TEXT,
        active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT (datetime('now','localtime')),
        last_login DATETIME
      )
    `);

    // ─── 제품 등록 테이블 ─────────────────────────────────────────────
    database.run(`
      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_code TEXT NOT NULL,
        model_name TEXT NOT NULL,
        lot_no TEXT NOT NULL,
        barcode_short TEXT,
        barcode_long TEXT,
        barcode_size TEXT,
        maker TEXT,
        quantity INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'Roll',
        manufacture_date DATE,
        expiry_date DATE,
        shipment_date DATE,
        notes TEXT,
        registered_by INTEGER,
        created_at DATETIME DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (registered_by) REFERENCES users(id)
      )
    `);

    // ─── 검사 세션 테이블 ─────────────────────────────────────────────
    database.run(`
      CREATE TABLE IF NOT EXISTS inspection_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_code TEXT UNIQUE,
        product_id INTEGER,
        material_code TEXT,
        model_name TEXT,
        lot_no TEXT,
        shipment_date DATE,
        total_quantity INTEGER DEFAULT 0,
        inspected_count INTEGER DEFAULT 0,
        pass_count INTEGER DEFAULT 0,
        fail_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress','completed','cancelled')),
        inspector_id INTEGER,
        inspector_name TEXT,
        started_at DATETIME DEFAULT (datetime('now','localtime')),
        completed_at DATETIME,
        notes TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (inspector_id) REFERENCES users(id)
      )
    `);

    // ─── 검사 기록 테이블 ─────────────────────────────────────────────
    database.run(`
      CREATE TABLE IF NOT EXISTS inspection_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no INTEGER,
        session_id INTEGER,
        inspection_date DATE DEFAULT (date('now','localtime')),
        inspection_time TIME DEFAULT (time('now','localtime')),
        inspector_id INTEGER,
        inspector_name TEXT,
        production_lot_no TEXT,
        material_code TEXT,
        model_name TEXT,
        shipment_date DATE,
        scanned_value TEXT,
        expected_value TEXT,
        scan_type TEXT,
        result TEXT CHECK(result IN ('PASS','FAIL')),
        fail_reason TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (session_id) REFERENCES inspection_sessions(id),
        FOREIGN KEY (inspector_id) REFERENCES users(id)
      )
    `);

    // ─── 시스템 설정 테이블 ───────────────────────────────────────────
    database.run(`
      CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT,
        updated_by INTEGER,
        updated_at DATETIME DEFAULT (datetime('now','localtime'))
      )
    `);

    // ─── 감사 로그 ────────────────────────────────────────────────────
    database.run(`
      CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        action TEXT,
        target_table TEXT,
        target_id INTEGER,
        detail TEXT,
        ip_address TEXT,
        created_at DATETIME DEFAULT (datetime('now','localtime'))
      )
    `);

    // ─── 기본 관리자 계정 ─────────────────────────────────────────────
    const adminPwd = bcrypt.hashSync('admin1234', 10);
    database.run(`
      INSERT OR IGNORE INTO users (username, password, name, role, department)
      VALUES ('admin', ?, '시스템관리자', 'admin', 'IT')
    `, [adminPwd]);

    const inspectorPwd = bcrypt.hashSync('inspector1234', 10);
    database.run(`
      INSERT OR IGNORE INTO users (username, password, name, role, department)
      VALUES ('inspector01', ?, '검사원1', 'inspector', '품질관리팀')
    `, [inspectorPwd]);

    // ─── 기본 설정 ────────────────────────────────────────────────────
    const defaultSettings = [
      ['company_name', '검사기록관리 시스템', '회사/시스템 이름'],
      ['system_version', 'v01', '시스템 버전'],
      ['barcode_type_1', 'material_code', '바코드 타입1 필드'],
      ['barcode_type_2', 'lot_no_long', '바코드 타입2 필드'],
      ['barcode_type_3', 'lot_no_short', '바코드 타입3 필드'],
      ['auto_sequence', 'true', '자동 순번 사용'],
    ];
    defaultSettings.forEach(([key, value, desc]) => {
      database.run(
        `INSERT OR IGNORE INTO system_settings (key, value, description) VALUES (?, ?, ?)`,
        [key, value, desc]
      );
    });

    console.log('✅ 데이터베이스 초기화 완료');
  });
}

module.exports = { getDb, initDatabase };
