document.getElementById('scan-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const target = document.getElementById('target').value;
  const scanType = document.getElementById('scan-type').value;
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');

  loading.style.display = 'block';
  result.textContent = '';

  try {
    // Step 1: Start the scan
    const response = await fetch('http://localhost:8000/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ target: target, scan_type: scanType })
    });

    if (!response.ok) {
      throw new Error('Failed to start scan');
    }

    const scanData = await response.json();
    
    if (scanData.status === 'error') {
      throw new Error(scanData.message);
    }

    const taskId = scanData.task_id;
    result.textContent = `Scan started! Task ID: ${taskId}\nStatus: ${scanData.status}\n\nMonitoring scan progress...`;

    // Step 2: Poll for scan completion
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes (5 seconds per attempt)
    
    const pollInterval = setInterval(async () => {
      attempts++;
      
      try {
        const statusResponse = await fetch(`http://localhost:8000/scan-status/${taskId}`);
        const statusData = await statusResponse.json();
        
        if (statusData.status === 'error') {
          clearInterval(pollInterval);
          loading.style.display = 'none';
          result.textContent = `Error: ${statusData.message}`;
          return;
        }
        
        // Update status
        result.textContent = `Scan in progress...\nTask ID: ${taskId}\nStatus: ${statusData.status}\nAttempts: ${attempts}/${maxAttempts}`;
        
        // Check if scan is complete
        if (statusData.status === 'Done') {
          clearInterval(pollInterval);
          
          // Step 3: Get results
          const resultsResponse = await fetch(`http://localhost:8000/scan-results/${taskId}`);
          const resultsData = await resultsResponse.json();
          
          loading.style.display = 'none';
          
          if (resultsData.status === 'completed') {
            let output = `Scan complete!\nTarget: ${target}\nType: ${scanType}\nTask ID: ${taskId}\n\n`;
            
            if (resultsData.vulnerabilities && resultsData.vulnerabilities.length > 0) {
              output += `Vulnerabilities found (${resultsData.vulnerabilities.length}):\n`;
              resultsData.vulnerabilities.forEach((vuln, index) => {
                output += `${index + 1}. ${vuln.name} (${vuln.severity})\n`;
              });
            } else {
              output += 'No vulnerabilities found.';
            }
            
            result.textContent = output;
          } else {
            result.textContent = `Error retrieving results: ${resultsData.message}`;
          }
        }
        
        // Timeout after max attempts
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          loading.style.display = 'none';
          result.textContent = `Scan timeout after ${maxAttempts} attempts.\nTask ID: ${taskId}\nLast Status: ${statusData.status}`;
        }
        
      } catch (error) {
        clearInterval(pollInterval);
        loading.style.display = 'none';
        result.textContent = `Error polling scan status: ${error.message}`;
      }
    }, 5000); // Check every 5 seconds
    
  } catch (err) {
    loading.style.display = 'none';
    result.textContent = 'Error: ' + err.message;
  }
});

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