CREATE TRIGGER issues_trigger_update
AFTER UPDATE ON issues
BEGIN
  /* The cached value of 'max_open' may now be invalid */
  DELETE FROM cached WHERE name = 'max_open';
END;
