class QuizClient {
    constructor() {
        this.username = '';
        this.score = 0;
        this.currentQuestion = null;
        this.startTime = null;
        this.timeLeft = 30;
        this.timerInterval = null; // holds the active countdown interval
        this.init();
    }
    
    init() {
        this.joinBtn = document.getElementById('join-btn');
        this.usernameInput = document.getElementById('username-input');
        
        this.joinBtn.addEventListener('click', () => this.connect());
        this.usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.connect();
        });
        
        this.startPolling();
    }
    
    async connect() {
        const username = this.usernameInput.value.trim();
        if (!username) return alert('Please enter a username');
        
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'username=' + encodeURIComponent(username)
        });
        
        const data = await response.json();
        if (data.success) {
            this.username = username;
            document.getElementById('player-name').textContent = username;
            document.getElementById('login-screen').classList.remove('active');
            document.getElementById('game-screen').classList.add('active');
        }
    }
    
    startPolling() {
        setInterval(async () => {
            const response = await fetch('/api/messages');
            const data = await response.json();
            data.messages.forEach(msg => this.handleMessage(msg));
        }, 500);
    }
    
    handleMessage(msg) {
        if (msg.type === 'game_start') {
            document.getElementById('waiting-room').style.display = 'none';
        } else if (msg.type === 'question') {
            // hide waiting/leaderboard when a new question arrives
            document.getElementById('wait-screen').style.display = 'none';
            document.getElementById('leaderboard').style.display = 'none';
            this.showQuestion(msg);
        } else if (msg.type === 'result') {
            this.showResult(msg);
        } else if (msg.type === 'leaderboard') {
            this.showLeaderboard(msg.top3);
        } else if (msg.type === 'wait') {
            this.showWait(msg);
        } else if (msg.type === 'end') {
            this.showFinalResults(msg);
        }
    }
    
    showQuestion(q) {
        // clear any previous timers before starting a new question
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        this.currentQuestion = q;
        this.startTime = Date.now();
        this.timeLeft = 30;
        
        document.getElementById('question-area').style.display = 'block';
        document.getElementById('question-number').textContent = 'Question ' + q.number + '/10';
        document.getElementById('question-text').textContent = q.text;
        document.getElementById('result-message').textContent = '';
        
        const options = document.getElementById('options');
        options.innerHTML = '';
        q.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = opt;
            btn.onclick = () => this.submitAnswer(opt.charAt(0));
            options.appendChild(btn);
        });
        
        this.startTimer();
    }
    
    startTimer() {
        const timerEl = document.getElementById('timer');
        // start a fresh interval and store the handle so we can clear it later
        this.timerInterval = setInterval(() => {
            this.timeLeft--;
            timerEl.textContent = this.timeLeft + 's';
            if (this.timeLeft <= 0) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        }, 1000);
    }
    
    async submitAnswer(answer) {
        const timeTaken = (Date.now() - this.startTime) / 1000;
        
        await fetch('/api/answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question_id: this.currentQuestion.id,
                answer: answer,
                time: timeTaken
            })
        });
        
        document.querySelectorAll('.option-btn').forEach(btn => btn.disabled = true);
    }
    
    showResult(result) {
        this.score = result.total_score;
        document.getElementById('player-score').textContent = 'Score: ' + this.score;
        
        const msg = document.getElementById('result-message');
        if (result.is_correct) {
            msg.textContent = '✓ Correct! +' + result.points + ' points';
            msg.className = 'correct';
        } else {
            msg.textContent = '✗ Wrong. Correct: ' + result.correct;
            msg.className = 'incorrect';
        }
    }
    
    showWait(info) {
        // hide question and leaderboard
        document.getElementById('question-area').style.display = 'none';
        document.getElementById('leaderboard').style.display = 'none';
        document.getElementById('final-results').style.display = 'none';
        document.getElementById('waiting-room').style.display = 'none';
        
        // update wait stats
        document.getElementById('wait-rank').textContent = info.rank != null ? ('#' + info.rank) : '-';
        document.getElementById('wait-last-points').textContent = info.last_points;
        document.getElementById('wait-total').textContent = info.total_score;
        
        // show waiting screen
        document.getElementById('wait-screen').style.display = 'block';
    }
    
    showLeaderboard(top3) {
        // Only show leaderboard if wait screen is not active
        const waitScreen = document.getElementById('wait-screen');
        if (waitScreen.style.display === 'block') {
            // Wait screen is active, don't show leaderboard separately
            return;
        }
        
        const list = document.getElementById('leaderboard-list');
        list.innerHTML = '';
        top3.forEach((p, i) => {
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            item.innerHTML = '<span>' + (i+1) + '. ' + p.u + '</span><span>' + p.s + '</span>';
            list.appendChild(item);
        });
        document.getElementById('leaderboard').style.display = 'block';
    }
    
    showFinalResults(data) {
        // clear any running timer at game end
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        document.getElementById('question-area').style.display = 'none';
        document.getElementById('leaderboard').style.display = 'none';
        
        document.getElementById('winner-announcement').textContent = '👑 Winner: ' + data.winner;
        
        const list = document.getElementById('final-leaderboard');
        list.innerHTML = '';
        data.leaderboard.forEach((p, i) => {
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            item.innerHTML = '<span>' + (i+1) + '. ' + p.u + '</span><span>' + p.s + ' pts</span>';
            list.appendChild(item);
        });
        
        document.getElementById('final-results').style.display = 'block';
    }
}

new QuizClient();
