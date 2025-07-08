document.getElementById('scan-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const target = document.getElementById('target').value;
  const scanType = document.getElementById('scan-type').value;
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');

  loading.style.display = 'block';
  result.textContent = '';

  try {
    const response = await fetch('http://localhost:8000/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ target: target, scan_type: scanType })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    loading.style.display = 'none';
    let output = `Scan complete!\nTarget: ${data.target}\nType: ${data.scan_type}\n\nVulnerabilities found:`;
    if (data.result && data.result.length > 0) {
      data.result.forEach(vuln => {
        output += `\n- ${vuln.cve}: ${vuln.desc}`;
      });
    } else {
      output += '\nNone found.';
    }
    result.textContent = output;
  } catch (err) {
    loading.style.display = 'none';
    result.textContent = 'Error: ' + err.message;
  }
}); 