document.getElementById('scan-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  console.log('Form submitted!');
  
  const target = document.getElementById('target').value;
  console.log('Target:', target);
  
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');

  loading.style.display = 'block';
  result.textContent = '';

  try {
    console.log('Making request to:', 'http://localhost:8000/scan');
    console.log('Request payload:', { target: target });
    
    // Step 1: Start the scan
    const response = await fetch('http://localhost:8000/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ target: target })
    });

    console.log('Response received:', response);
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response not ok:', errorText);
      throw new Error(`Failed to start scan: ${response.status} ${errorText}`);
    }

    const scanData = await response.json();
    console.log('Scan data:', scanData);
    
    if (scanData.status === 'error') {
      throw new Error(scanData.message);
    }

    const taskId = scanData.task_id;
    result.textContent = `Scan started! Target: ${target}\nTask ID: ${taskId}\nStatus: ${scanData.status}\n\nMonitoring scan progress...`;

    // Step 2: Poll for scan completion
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes (5 seconds per attempt)
    
    const pollInterval = setInterval(async () => {
      attempts++;
      console.log(`Polling attempt ${attempts}/${maxAttempts}`);
      
      try {
        const statusResponse = await fetch(`http://localhost:8000/scan-status/${taskId}`);
        const statusData = await statusResponse.json();
        console.log('Status data:', statusData);
        
        if (statusData.status === 'error') {
          clearInterval(pollInterval);
          loading.style.display = 'none';
          result.textContent = `Error: ${statusData.message}`;
          return;
        }
        
        // Update status
        result.textContent = `Scan in progress...\nTarget: ${target}\nTask ID: ${taskId}\nStatus: ${statusData.status}\nAttempts: ${attempts}/${maxAttempts}`;
        
        // Check if scan is complete
        if (statusData.status === 'Done') {
          clearInterval(pollInterval);
          
          // Step 3: Get results
          const resultsResponse = await fetch(`http://localhost:8000/scan-results/${taskId}`);
          const resultsData = await resultsResponse.json();
          console.log('Results data:', resultsData);
          
          loading.style.display = 'none';
          
          if (resultsData.status === 'completed') {
            let output = `Scan complete!\nTarget: ${target}\nTask ID: ${taskId}\n\n`;
            
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
        console.error('Polling error:', error);
        clearInterval(pollInterval);
        loading.style.display = 'none';
        result.textContent = `Error polling scan status: ${error.message}`;
      }
    }, 5000); // Check every 5 seconds
    
  } catch (err) {
    console.error('Main error:', err);
    loading.style.display = 'none';
    result.textContent = 'Error: ' + err.message;
  }
});

// Add a test connection button (enabled for debugging)
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
    console.log('Testing connection to OpenVAS...');
    
    try {
      const response = await fetch('http://localhost:8000/test-connection');
      const data = await response.json();
      console.log('Test connection response:', data);
      
      if (data.status === 'success') {
        result.textContent = `✅ Connection successful!\nOpenVAS Version: ${data.version}`;
      } else {
        result.textContent = `❌ Connection failed: ${data.message}`;
      }
    } catch (error) {
      console.error('Test connection error:', error);
      result.textContent = `❌ Connection error: ${error.message}`;
    }
  });
  
  container.appendChild(testButton);
}

// Enable test button for debugging
addTestButton();

// Add a simple test button
function addSimpleTestButton() {
  const container = document.querySelector('.container');
  const simpleTestButton = document.createElement('button');
  simpleTestButton.textContent = 'Test Backend (Simple)';
  simpleTestButton.style.marginTop = '0.5rem';
  simpleTestButton.style.padding = '0.5rem 1rem';
  simpleTestButton.style.background = '#007bff';
  simpleTestButton.style.color = 'white';
  simpleTestButton.style.border = 'none';
  simpleTestButton.style.borderRadius = '0.5rem';
  simpleTestButton.style.cursor = 'pointer';
  
  simpleTestButton.addEventListener('click', async () => {
    const result = document.getElementById('result');
    result.textContent = 'Testing simple backend connection...';
    console.log('Testing simple backend connection...');
    
    try {
      const response = await fetch('http://localhost:8000/');
      const data = await response.json();
      console.log('Simple test response:', data);
      result.textContent = `✅ Backend is running!\nMessage: ${data.message}`;
    } catch (error) {
      console.error('Simple test error:', error);
      result.textContent = `❌ Backend error: ${error.message}`;
    }
  });
  
  container.appendChild(simpleTestButton);
}

addSimpleTestButton(); 