<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<html>
<head>
    <title>Issue Agent</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <h1>🤖 Issue Agent</h1>
        <p class="subtitle">AI가 찾아주는 맞춤형 이슈 알림 서비스</p>

        <form id="issue-form">
            <div>
                <label for="keywords">🔍 검색 키워드</label>
                <input type="text" id="keywords" name="keywords"
                       placeholder="검색할 키워드를 입력하세요 (쉼표로 구분)">
            </div>
            <div>
                <label for="platforms">🌐 플랫폼</label>
                <input type="text" id="platforms" name="platforms"
                       placeholder="예: google, reddit, asec">
            </div>
            <div>
                <label for="detail">✨ 상세 조건 (선택)</label>
                <textarea id="detail" name="detail" rows="3"
                          placeholder="예: 랜섬웨어, 보안 이슈, API 문서 등 원하는 상세 조건을 입력하세요"></textarea>
            </div>
            <button type="submit">🚀 검색 시작하기</button>
        </form>

        <div id="results-container">
            <div class="spinner" id="loading-spinner"></div>
            <div id="results"></div>

            <!-- Confirm Agent Button (shown after results) -->
            <button id="confirm-agent-btn">🤖 Confirm Agent - 나만의 알림봇 만들기!</button>
        </div>
    </div>

    <!-- Agent Creation Modal -->
    <div id="agent-modal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>

            <div id="robot-animation-container" style="display:none;">
                <div class="robot-animation">
                    <div class="robot">🤖</div>
                    <div class="success-message">나만의 Agent 완성!</div>
                </div>
            </div>

            <div id="agent-form-container">
                <h2>이슈 알림봇 설정</h2>
                <p>새로운 이슈가 발견되면 이메일로 알림을 보내드립니다!</p>

                <form id="agent-creation-form" class="modal-form">
                    <div class="form-group">
                        <label for="user-email">이메일 주소</label>
                        <input type="email" id="user-email" name="email" required
                               placeholder="your@email.com">
                        <div class="help-text">알림을 받을 이메일 주소를 입력하세요</div>
                    </div>

                    <div class="form-group">
                        <label for="notification-time">알림 시간</label>
                        <input type="time" id="notification-time" name="time" required
                               value="09:00">
                        <div class="help-text">매일 이 시간에 새로운 결과를 확인하여 알림을 보냅니다</div>
                    </div>

                    <button type="submit">🚀 Agent 생성하기!</button>
                </form>
            </div>
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

            //유효성 검사
            if (form.keywords.value=="") {
                alert("검색할 키워드를 입력해주세요.");
                return;
            } else if (form.platforms.value=="") {
                alert("검색할 플랫폼을 입력해주세요.");
                return;
            }

            spinner.style.display = 'block';
            resultsEl.textContent = 'Running agent...';
            runAgentButton.disabled = true;
            //runAgentButton.style.backgroundColor = '#6c757d';

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

                    let outputHtml = '<h2>Results</h2>';

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

                    // Show Confirm Agent button after successful results
                    if (results.total_results > 0) {
                        document.getElementById('confirm-agent-btn').style.display = 'block';
                    }
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
                runAgentButton.style.backgroundColor = '#719df3';
            }
        });

        // ============================================
        // Agent Creation Modal Logic
        // ============================================

        var lastSearchData = null;  // Store last search parameters

        var modal = document.getElementById('agent-modal');
        var confirmBtn = document.getElementById('confirm-agent-btn');
        var closeBtn = document.getElementsByClassName('close')[0];
        var agentForm = document.getElementById('agent-creation-form');
        var robotAnimationContainer = document.getElementById('robot-animation-container');
        var agentFormContainer = document.getElementById('agent-form-container');

        // Open modal when clicking Confirm Agent button
        confirmBtn.onclick = function() {
            modal.style.display = 'block';
            robotAnimationContainer.style.display = 'none';
            agentFormContainer.style.display = 'block';

            // Store current search data
            var formData = new FormData(form);
            lastSearchData = {
                keywords: formData.get('keywords').split(',').map(function(k) { return k.trim(); }).filter(function(k) { return k; }),
                platforms: formData.get('platforms').split(',').map(function(p) { return p.trim(); }).filter(function(p) { return p; }),
                detail: formData.get('detail') || ''
            };
        };

        // Close modal
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };

        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };

        // Handle agent creation form submission
        agentForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            var email = document.getElementById('user-email').value;
            var notificationTime = document.getElementById('notification-time').value;

            console.log('Creating agent subscription...', email, notificationTime);

            try {
                // Create subscription via API
                var subscriptionData = {
                    email: email,
                    notification_time: notificationTime,
                    keywords: lastSearchData.keywords,
                    platforms: lastSearchData.platforms,
                    detail: lastSearchData.detail
                };

                var response = await fetch('http://localhost:5000/api/subscriptions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(subscriptionData)
                });

                if (!response.ok) {
                    throw new Error('Failed to create subscription');
                }

                var result = await response.json();
                console.log('Subscription created:', result);

                // Show robot animation
                agentFormContainer.style.display = 'none';
                robotAnimationContainer.style.display = 'block';

                // Auto-close modal after 3 seconds
                setTimeout(function() {
                    modal.style.display = 'none';
                    alert('이슈 알림봇이 생성되었습니다! ' + email + ' 으로 매일 ' + notificationTime + ' 에 알림을 보내드립니다.');
                }, 3000);

            } catch (error) {
                console.error('Error creating subscription:', error);
                alert('구독 생성 실패: ' + error.message);
            }
        });

    //]]>
    </script>

</body>
</html>