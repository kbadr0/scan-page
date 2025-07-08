document.getElementById('scan-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const target = document.getElementById('target').value;
  const scanType = document.getElementById('scan-type').value;
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');

  loading.style.display = 'block';
  result.textContent = '';

  // Simulate API call
  setTimeout(() => {
    loading.style.display = 'none';
    result.textContent = `Scan complete!\nTarget: ${target}\nType: ${scanType}\n\nVulnerabilities found:\n- CVE-2023-1234: Example Vulnerability\n- CVE-2022-5678: Another Example`;
  }, 2500);
}); 