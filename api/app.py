# app.py
from flask import Flask, jsonify
import statsapi
import pandas as pd

app = Flask(__name__)

# 將前端 HTML + JS 宣告為 Python 多行字串變數
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2026 MLB 數據深度分析看板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-light">

    <div class="container py-5">
        <h1 class="mb-4 text-center fw-bold">2026 MLB 球隊戰績與運氣指數分析</h1>
        <p class="text-muted text-center">單一 app.py 架構：Python (Pandas) 後端計算，前端 JS 實時動態渲染</p>

        <div class="row my-4">
            <div class="col-12 card shadow-sm p-4">
                <canvas id="mlbChart" style="width: 100%; height: 400px;"></canvas>
            </div>
        </div>

        <div class="row">
            <div class="col-12 card shadow-sm p-4">
                <h3 class="mb-3">深度數據表格</h3>
                <div class="table-responsive">
                    <table class="table table-hover" id="dataTable">
                        <thead class="table-dark">
                            <tr>
                                <th>球隊</th>
                                <th>分區</th>
                                <th>勝 - 敗</th>
                                <th>實際勝率</th>
                                <th>運氣指數 (Luck Factor)</th>
                            </tr>
                        </thead>
                        <tbody>
                            </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 網頁載入後，直接向同一個檔案的 /api/analysis 路由要資料
        fetch('/api/analysis')
            .then(response => response.json())
            .then(res => {
                if(res.status === 'success') {
                    renderPage(res.data);
                } else {
                    alert('資料載入失敗: ' + res.message);
                }
            });

        function renderPage(data) {
            const tableBody = document.querySelector('#dataTable tbody');
            const labels = [];
            const luckFactors = [];

            data.forEach(team => {
                // 1. 填充表格
                const row = `
                    <tr>
                        <td class="fw-bold">${team.team_name}</td>
                        <td>${team.division}</td>
                        <td>${team.w} - ${team.l}</td>
                        <td>${(team.actual_win_pct * 100).toFixed(1)}%</td>
                        <td class="${team.luck_factor >= 0 ? 'text-success' : 'text-danger'}">
                            ${team.luck_factor >= 0 ? '+' : ''}${(team.luck_factor * 100).toFixed(1)}%
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;

                // 2. 準備圖表資料
                labels.push(team.team_name);
                luckFactors.push((team.luck_factor * 100).toFixed(2));
            });

            // 3. 繪製 Chart.js 圖表
            const ctx = document.getElementById('mlbChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels.slice(0, 15), // 先取前 15 名避免圖表太擠
                    datasets: [{
                        label: '運氣成分 % (正值代表實際戰績高於預期)',
                        data: luckFactors.slice(0, 15),
                        backgroundColor: luckFactors.slice(0, 15).map(val => val >= 0 ? 'rgba(40, 167, 69, 0.6)' : 'rgba(220, 53, 69, 0.6)'),
                        borderColor: luckFactors.slice(0, 15).map(val => val >= 0 ? 'rgb(40, 167, 69)' : 'rgb(220, 53, 69)'),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    </script>
</body>
</html>
"""

# 路由 1：首頁，直接回傳剛剛宣告的 HTML 字串
@app.route('/')
def index():
    return FRONTEND_HTML

# 路由 2：後端 API，負責抓取 MLB 資料並進行 Pandas 深度分析
@app.route('/api/analysis')
def get_mlb_analysis():
    try:
        # 抓取 2026 球季原始戰績 (103: 美聯, 104: 國聯)
        standings_data = statsapi.standings_data(leagueId="103,104", season=2026)
        
        raw_teams = []
        for div_id, div_info in standings_data.items():
            div_name = div_info['div_name']
            for team in div_info['teams']:
                raw_teams.append({
                    'division': div_name,
                    'team_name': team['name'],
                    'w': team['w'],
                    'l': team['l'],
                    'rs': team.get('rs', 0), # 得分 Runs Scored
                    'ra': team.get('ra', 0)  # 失分 Runs Against
                })
        
        # 載入 Pandas 進行數據分析
        df = pd.DataFrame(raw_teams)
        
        if not df.empty and 'rs' in df.columns and df['rs'].sum() > 0:
            # 運動分析學進階指標：畢達哥拉斯期望勝率 (實力評估)
            df['expected_win_pct'] = (df['rs']**2) / (df['rs']**2 + df['ra']**2)
            df['actual_win_pct'] = df['w'] / (df['w'] + df['l'])
            # 實際勝率 - 期望勝率 = 運氣成分
            df['luck_factor'] = df['actual_win_pct'] - df['expected_win_pct']
        else:
            df['actual_win_pct'] = df['w'] / (df['w'] + df['l'])
            df['luck_factor'] = 0
            
        # 依實際勝率排序
        df = df.sort_values(by='actual_win_pct', ascending=False)
        
        return jsonify({"status": "success", "data": df.to_dict(orient='records')})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)