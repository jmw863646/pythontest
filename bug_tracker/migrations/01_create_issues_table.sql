CREATE TABLE issues(
  id INTEGER PRIMARY KEY,
  title VARCHAR(255),
  description TEXT,
  opened_datetime DATETIME DEFAULT (datetime('now')),
  closed_datetime DATETIME,
  creatorId INTEGER NOT NULL,
  assigneeId INTEGER,
  FOREIGN KEY(creatorId) REFERENCES users(id),
  FOREIGN KEY(assigneeId) REFERENCES users(id)
);
