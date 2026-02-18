/**
 * Database module providing connectivity status.
 * isConnected() returns true when the database is reachable.
 */

let connected = false;

function isConnected() {
  return connected;
}

function setConnected(value) {
  connected = value;
}

module.exports = { isConnected, setConnected };
