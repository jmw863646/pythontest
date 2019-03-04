CREATE TABLE users(
  id INTEGER PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  password VARCHAR(255),
  uuid CHAR(32),
  expiresAt DATETIME
);
