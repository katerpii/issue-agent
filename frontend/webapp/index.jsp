<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<html>
<head>
    <title>Issue Agent Web UI</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 2rem; background-color: #f8f9fa; color: #333; }
        .container { max-width: 800px; margin: 0 auto; background-color: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1, h2 { color: #007BFF; }
        h1 { text-align: center; }
        form { display: grid; grid-template-columns: 1fr; gap: 1rem; }
        label { font-weight: bold; }
        input[type="text"], input[type="date"], textarea { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { padding: 0.75rem 1.5rem; font-size: 1rem; cursor: pointer; background-color: #007BFF; color: white; border: none; border-radius: 4px; transition: background-color 0.2s; }
        button:hover { background-color: #0056b3; }
        #results-container { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }
        #results { white-space: pre-wrap; background-color: #f1f3f5; padding: 1rem; border-radius: 4px; word-wrap: break-word; }
        .spinner { display: none; margin: 1rem auto; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <div class="container">
        <h1>Issue Agent</h1>
        <p style="text-align: center; margin-bottom: 2rem;">Enter your search criteria below to find relevant issues across different platforms.</p>

        <form id="issue-form">
            <div>
                <label for="keywords">Keywords (comma-separated):</label>
                <input type="text" id="keywords" name="keywords" required value="gemini 1.5">
            </div>
            <div>
                <label for="platforms">Platforms (comma-separated, e.g., google, reddit):</label>
                <input type="text" id="platforms" name="platforms" required value="google">
            </div>
            <div>
                <label for="start_date">Start Date:</label>
                <input type="date" id="start_date" name="start_date" required>
            </div>
            <div>
                <label for="end_date">End Date:</label>
                <input type="date" id="end_date" name="end_date" required>
            </div>
            <div>
                <label for="detail">Detail (optional):</label>
                <textarea id="detail" name="detail" rows="3"></textarea>
            </div>
            <button type="submit">Run Agent</button>
        </form>

        <div id="results-container">
            <h2>Results</h2>
            <div class="spinner" id="loading-spinner"></div>
            <pre id="results">(Results will appear here)</pre>
        </div>
    </div>

    <script>
        // Set default dates to today and a week ago
        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date();
            const aWeekAgo = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7);
            document.getElementById('end_date').valueAsDate = today;
            document.getElementById('start_date').valueAsDate = aWeekAgo;
        });

        const form = document.getElementById('issue-form');
        const resultsEl = document.getElementById('results');
        const spinner = document.getElementById('loading-spinner');
        const runAgentButton = form.querySelector('button');

        // Backend API URL
        const runApiUrl = 'http://localhost:5000/api/run';

        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            spinner.style.display = 'block';
            resultsEl.textContent = 'Running agent...';
            runAgentButton.disabled = true;
            runAgentButton.style.backgroundColor = '#6c757d';

            const formData = new FormData(form);
            const data = {
                keywords: formData.get('keywords').split(',').map(k => k.trim()).filter(k => k),
                platforms: formData.get('platforms').split(',').map(p => p.trim()).filter(p => p),
                start_date: formData.get('start_date'),
                end_date: formData.get('end_date'),
                detail: formData.get('detail')
            };

            try {
                const response = await fetch(runApiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }

                const responseData = await response.json();
                
                if (responseData.results && responseData.results.length > 0) {
                    resultsEl.textContent = JSON.stringify(responseData.results, null, 2);
                } else {
                    resultsEl.textContent = 'No results found.';
                }

            } catch (error) {
                console.error('Error running agent:', error);
                resultsEl.textContent = `Error: ${error.message}`;
            } finally {
                spinner.style.display = 'none';
                runAgentButton.disabled = false;
                runAgentButton.style.backgroundColor = '#007BFF';
            }
        });
    </script>

</body>
</html>