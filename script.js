// --- Multi-scan management ---
// Store all running scans in a map: { taskId: { target, status, interval, ... } }
const scanList = document.getElementById('scan-list');
const scans = {};

document.getElementById('scan-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const target = document.getElementById('target').value;
  // UI feedback
  document.getElementById('loading').style.display = 'block';
  document.getElementById('result').textContent = '';

  try {
    // Start the scan
    const response = await fetch('http://localhost:8000/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target })
    });
    if (!response.ok) throw new Error('Failed to start scan');
    const scanData = await response.json();
    if (scanData.status === 'error') throw new Error(scanData.message);
    const taskId = scanData.task_id;

    // Create scan entry in the list
    addScanToList({ target, taskId, status: scanData.status });
    document.getElementById('loading').style.display = 'none';
    document.getElementById('result').textContent = '';
  } catch (err) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('result').textContent = 'Error: ' + err.message;
  }
});

// Add a scan to the scan list UI and start polling
function addScanToList({ target, taskId, status }) {
  // Create list item
  const li = document.createElement('li');
  li.style.marginBottom = '1rem';
  li.style.background = '#222';
  li.style.padding = '1rem';
  li.style.borderRadius = '0.5rem';
  li.style.display = 'flex';
  li.style.alignItems = 'center';
  li.style.justifyContent = 'space-between';
  li.id = `scan-${taskId}`;

  // Scan info
  const info = document.createElement('span');
  info.textContent = `Target: ${target} | Status: ${status}`;
  info.style.flex = '1';

  // Stop button
  const stopBtn = document.createElement('button');
  stopBtn.textContent = 'Stop';
  stopBtn.style.background = '#dc3545';
  stopBtn.style.color = 'white';
  stopBtn.style.border = 'none';
  stopBtn.style.borderRadius = '0.5rem';
  stopBtn.style.padding = '0.5rem 1rem';
  stopBtn.style.marginLeft = '1rem';
  stopBtn.style.cursor = 'pointer';

  // Polling interval for this scan
  let attempts = 0;
  const maxAttempts = 60;
  const pollInterval = setInterval(async () => {
    attempts++;
    try {
      const statusResponse = await fetch(`http://localhost:8000/scan-status/${taskId}`);
      const statusData = await statusResponse.json();
      if (statusData.status === 'error') {
        clearInterval(pollInterval);
        info.textContent = `Target: ${target} | Status: error | ${statusData.message}`;
        stopBtn.disabled = true;
        return;
      }
      info.textContent = `Target: ${target} | Status: ${statusData.status} | Attempt: ${attempts}/${maxAttempts}`;
      // If scan is done, fetch results
      if (statusData.status === 'Done') {
        clearInterval(pollInterval);
        stopBtn.disabled = true;
        const resultsResponse = await fetch(`http://localhost:8000/scan-results/${taskId}`);
        const resultsData = await resultsResponse.json();
        if (resultsData.status === 'completed') {
          info.textContent = `Target: ${target} | Status: Done | Results: ${resultsData.vulnerabilities.length} vulnerabilities`;
        } else {
          info.textContent = `Target: ${target} | Status: Done | Error: ${resultsData.message}`;
        }
      }
      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        info.textContent = `Target: ${target} | Status: timeout after ${maxAttempts} attempts.`;
        stopBtn.disabled = true;
      }
    } catch (error) {
      clearInterval(pollInterval);
      info.textContent = `Target: ${target} | Status: error | ${error.message}`;
      stopBtn.disabled = true;
    }
  }, 5000);

  // Stop button logic
  stopBtn.addEventListener('click', async function() {
    stopBtn.disabled = true;
    try {
      const response = await fetch(`http://localhost:8000/stop-scan/${taskId}`, { method: 'POST' });
      const data = await response.json();
      info.textContent = `Target: ${target} | Status: stopped | ${data.message}`;
      clearInterval(pollInterval);
    } catch (err) {
      info.textContent = `Target: ${target} | Status: error stopping scan | ${err.message}`;
    }
  });

  // Add to UI
  li.appendChild(info);
  li.appendChild(stopBtn);
  scanList.appendChild(li);

  // Track in scans map
  scans[taskId] = { target, status, interval: pollInterval, li };
}

// Add a test connection button (optional)
function addTestButton() {
  const container = document.querySelector('.container');
  const testButton = document.createElement('button');
  testButton.textContent = 'Test OpenVAS Connection';
  testButton.style.marginTop = '1rem';
  testButton.style.padding = '0.5rem 1rem';
  testButton.style.background = '#28a745';
  testButton.style.color = 'white';
  testButton.style.border = 'none';
  testButton.style.borderRadius = '0.5rem';
  testButton.style.cursor = 'pointer';
  
  testButton.addEventListener('click', async () => {
    const result = document.getElementById('result');
    result.textContent = 'Testing connection...';
    
    try {
      const response = await fetch('http://localhost:8000/test-connection');
      const data = await response.json();
      
      if (data.status === 'success') {
        result.textContent = `✅ Connection successful!\nOpenVAS Version: ${data.version}`;
      } else {
        result.textContent = `❌ Connection failed: ${data.message}`;
      }
    } catch (error) {
      result.textContent = `❌ Connection error: ${error.message}`;
    }
  });
  
  container.appendChild(testButton);
}

// Uncomment the next line to add the test button
// addTestButton(); 