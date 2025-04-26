let startTime = Date.now();

function resetTimer() {
  startTime = Date.now();
}

function getElapsedTime() {
  return ((Date.now() - startTime) / 1000).toFixed(2);  // seconds
}
