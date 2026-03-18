const express = require('express');
const cors = require('cors');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = process.env.PORT || 5000;

const dbPath = path.join(__dirname, 'database.sqlite');
const db = new sqlite3.Database(dbPath);

app.use(cors());
app.use(express.json());

db.serialize(() => {
  db.run(
    `CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`
  );
});

app.get('/api/entries', (req, res) => {
  db.all(
    'SELECT id, name, email, created_at FROM entries ORDER BY id DESC',
    [],
    (error, rows) => {
      if (error) {
        return res.status(500).json({ message: 'Failed to fetch entries.' });
      }

      return res.json(rows);
    }
  );
});

app.post('/api/entries', (req, res) => {
  const { name, email } = req.body;

  if (!name || !email) {
    return res.status(400).json({ message: 'Name and email are required.' });
  }

  const insertSql = 'INSERT INTO entries (name, email) VALUES (?, ?)';
  db.run(insertSql, [name.trim(), email.trim().toLowerCase()], function onInsert(error) {
    if (error) {
      return res.status(500).json({ message: 'Failed to save entry.' });
    }

    return res.status(201).json({
      id: this.lastID,
      name: name.trim(),
      email: email.trim().toLowerCase(),
    });
  });
});

app.put('/api/entries/:id', (req, res) => {
  const { id } = req.params;
  const { name, email } = req.body;

  if (!name || !email) {
    return res.status(400).json({ message: 'Name and email are required.' });
  }

  const updateSql = 'UPDATE entries SET name = ?, email = ? WHERE id = ?';
  db.run(updateSql, [name.trim(), email.trim().toLowerCase(), id], function onUpdate(error) {
    if (error) {
      return res.status(500).json({ message: 'Failed to update entry.' });
    }

    if (this.changes === 0) {
      return res.status(404).json({ message: 'Entry not found.' });
    }

    return res.json({
      id: Number(id),
      name: name.trim(),
      email: email.trim().toLowerCase(),
    });
  });
});

app.delete('/api/entries/:id', (req, res) => {
  const { id } = req.params;

  db.run('DELETE FROM entries WHERE id = ?', [id], function onDelete(error) {
    if (error) {
      return res.status(500).json({ message: 'Failed to delete entry.' });
    }

    if (this.changes === 0) {
      return res.status(404).json({ message: 'Entry not found.' });
    }

    return res.status(204).send();
  });
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
