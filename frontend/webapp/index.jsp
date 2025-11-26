<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<html>
<head>
    <title>Issue Agent Web UI</title>
    <link rel="stylesheet" href="css/style.css">
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
                <label for="detail">Detail (optional preferences for filtering):</label>
                <textarea id="detail" name="detail" rows="3" placeholder="e.g., 랜섬웨어, security issues, API documentation"></textarea>
            </div>
            <button type="submit">Run Agent</button>
        </form>

        <div id="results-container">
            <h2>Results</h2>
            <div class="spinner" id="loading-spinner"></div>
            <div id="results">(Results will appear here)</div>
        </div>
    </div>

    <script type="text/javascript">
    //<![CDATA[
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
                detail: formData.get('detail') || ''
            };

            try {
                console.log('Sending request to:', runApiUrl);
                console.log('Request data:', JSON.stringify(data, null, 2));

                const controller = new AbortController();
                const timeoutId = setTimeout(function() { controller.abort(); }, 60000);

                const response = await fetch(runApiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);
                console.log('Response status:', response.status);

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error('HTTP error! status: ' + response.status + ' - ' + (errorData.detail || 'Unknown error'));
                }

                const responseData = await response.json();
                console.log('Response data:', responseData);

                // results is now a dict with summary, total_results, and results_by_platform
                if (responseData.results) {
                    const results = responseData.results;

                    let outputHtml = '';

                    // Show summary
                    if (results.summary) {
                        outputHtml += '<div class="summary-section">';
                        outputHtml += '<h3>요약</h3>';
                        outputHtml += '<p>' + results.summary + '</p>';
                        outputHtml += '</div>';
                    }

                    // Show total
                    const totalResults = results.total_results || 0;
                    outputHtml += '<div class="total-results-section">';
                    outputHtml += '<h3>총 필터링된 결과</h3>';
                    outputHtml += '<p>' + totalResults + '건</p>';
                    outputHtml += '</div>';

                    // Show results by platform
                    if (results.results_by_platform) {
                        outputHtml += '<div class="platform-results-section">';
                        outputHtml += '<h2>플랫폼별 결과</h2>';
                        for (const [platform, items] of Object.entries(results.results_by_platform)) {
                            outputHtml += '<div class="platform-section">';
                            outputHtml += '<h3>' + platform.toUpperCase() + ' (' + items.length + '건)</h3>';
                            if (items.length > 0) {
                                outputHtml += '<ul>';
                                items.forEach(function(item, idx) {
                                    outputHtml += '<li class="result-item">';
                                    outputHtml += '<h4>[' + (idx + 1) + '] ' + item.title + '</h4>';
                                    outputHtml += '<p>URL: <a href="' + item.url + '" target="_blank">' + item.url + '</a></p>';
                                    if (item.relevance_score !== undefined) {
                                        outputHtml += '<p>관련성 점수: ' + item.relevance_score + '/10</p>';
                                    }
                                    if (item.relevance_reason) {
                                        outputHtml += '<p>이유: ' + item.relevance_reason + '</p>';
                                    }
                                    if (item.content && item.content.length > 0) {
                                        outputHtml += '<p>미리보기: ' + item.content.substring(0, 150) + '...</p>';
                                    }
                                    outputHtml += '</li>';
                                });
                                outputHtml += '</ul>';
                            } else {
                                outputHtml += '<p>결과 없음.</p>';
                            }
                            outputHtml += '</div>';
                        }
                        outputHtml += '</div>';
                    }

                    resultsEl.innerHTML = outputHtml || '결과를 찾을 수 없습니다.';
                } else {
                    resultsEl.innerHTML = '결과를 찾을 수 없습니다.';
                }

            } catch (error) {
                console.error('Error running agent:', error);
                console.error('Error details:', error);
                resultsEl.textContent = 'Error: ' + error.message + '\n\nCheck browser console for more details.';
            } finally {
                spinner.style.display = 'none';
                runAgentButton.disabled = false;
                runAgentButton.style.backgroundColor = '#007BFF';
            }
        });
    //]]>
    </script>

</body>
</html>