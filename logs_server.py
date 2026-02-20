#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер для отображения логов на порту 5002
"""

from flask import Flask, render_template_string, send_file
from pathlib import Path
import os

app = Flask(__name__)

LOGS_FILE = Path(__file__).parent / 'server.log'

LOG_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Логи сервера</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #252526;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        h1 {
            color: #4ec9b0;
            margin-bottom: 20px;
            font-size: 24px;
            border-bottom: 2px solid #3c3c3c;
            padding-bottom: 10px;
        }
        
        .controls {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        button {
            background: #0e639c;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #1177bb;
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .auto-refresh input {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .auto-refresh label {
            color: #cccccc;
            font-size: 14px;
        }
        
        .logs-container {
            background: #1e1e1e;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 15px;
            max-height: 80vh;
            overflow-y: auto;
            font-size: 13px;
        }
        
        .log-line {
            margin-bottom: 4px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .log-line.error {
            color: #f48771;
        }
        
        .log-line.warning {
            color: #dcdcaa;
        }
        
        .log-line.info {
            color: #4ec9b0;
        }
        
        .log-line.debug {
            color: #9cdcfe;
        }
        
        .status {
            color: #4ec9b0;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .empty-logs {
            color: #808080;
            text-align: center;
            padding: 40px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Логи сервера</h1>
        <div class="status" id="status">Загрузка логов...</div>
        <div class="controls">
            <button onclick="refreshLogs()">🔄 Обновить</button>
            <button onclick="clearLogs()">🗑️ Очистить логи</button>
            <div class="auto-refresh">
                <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()">
                <label for="autoRefresh">Автообновление (5 сек)</label>
            </div>
        </div>
        <div class="logs-container" id="logsContainer">
            <div class="empty-logs">Загрузка...</div>
        </div>
    </div>
    
    <script>
        let autoRefreshInterval = null;
        
        function getLogs() {
            fetch('/api/logs')
                .then(response => response.text())
                .then(data => {
                    const container = document.getElementById('logsContainer');
                    const status = document.getElementById('status');
                    
                    if (!data || data.trim() === '') {
                        container.innerHTML = '<div class="empty-logs">Логи пусты</div>';
                        status.textContent = 'Логи пусты';
                        return;
                    }
                    
                    const lines = data.split('\\n');
                    let html = '';
                    
                    lines.forEach(line => {
                        if (!line.trim()) return;
                        
                        let className = '';
                        if (line.includes('ERROR') || line.includes('Error') || line.includes('error')) {
                            className = 'error';
                        } else if (line.includes('WARNING') || line.includes('Warning') || line.includes('warning')) {
                            className = 'warning';
                        } else if (line.includes('INFO') || line.includes('Info') || line.includes('info')) {
                            className = 'info';
                        } else if (line.includes('DEBUG') || line.includes('Debug') || line.includes('debug')) {
                            className = 'debug';
                        }
                        
                        html += `<div class="log-line ${className}">${escapeHtml(line)}</div>`;
                    });
                    
                    container.innerHTML = html;
                    container.scrollTop = container.scrollHeight;
                    status.textContent = `Загружено строк: ${lines.length}`;
                })
                .catch(error => {
                    const container = document.getElementById('logsContainer');
                    container.innerHTML = `<div class="empty-logs error">Ошибка загрузки: ${error.message}</div>`;
                });
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function refreshLogs() {
            getLogs();
        }
        
        function clearLogs() {
            if (confirm('Вы уверены, что хотите очистить логи?')) {
                fetch('/api/clear_logs', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            getLogs();
                        } else {
                            alert('Ошибка при очистке логов: ' + (data.error || 'Неизвестная ошибка'));
                        }
                    })
                    .catch(error => {
                        alert('Ошибка при очистке логов: ' + error.message);
                    });
            }
        }
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(refreshLogs, 5000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }
        
        // Загружаем логи при загрузке страницы
        window.addEventListener('load', function() {
            getLogs();
        });
    </script>
</body>
</html>
"""

@app.route('/logs')
def logs():
    return render_template_string(LOG_TEMPLATE)

@app.route('/simple')
def simple():
    """Простая текстовая версия логов"""
    try:
        if LOGS_FILE.exists():
            with open(LOGS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Простой HTML шаблон для текстового отображения
            simple_template = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Логи (простая версия)</title>
    <style>
        body {{
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            background: #ffffff;
            color: #000000;
            padding: 20px;
            line-height: 1.4;
            font-size: 12px;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
        }}
    </style>
</head>
<body>
    <pre>{content}</pre>
</body>
</html>
"""
            return simple_template
        else:
            return "<html><body><pre>Файл логов не найден</pre></body></html>"
    except Exception as e:
        return f"<html><body><pre>Ошибка при чтении логов: {str(e)}</pre></body></html>"

@app.route('/')
def index():
    return render_template_string(LOG_TEMPLATE)

@app.route('/api/logs')
def get_logs():
    """Возвращает содержимое файла логов"""
    try:
        if LOGS_FILE.exists():
            with open(LOGS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return content
        else:
            return "Файл логов не найден"
    except Exception as e:
        return f"Ошибка при чтении логов: {str(e)}"

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    """Очищает файл логов"""
    try:
        if LOGS_FILE.exists():
            with open(LOGS_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            return {'success': True}
        else:
            return {'success': True, 'message': 'Файл логов не существует'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    print(f"Запуск сервера логов на http://localhost:5002/logs")
    app.run(debug=True, host='0.0.0.0', port=5002)
