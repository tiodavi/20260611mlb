# api/app.py
from flask import Flask, jsonify
import statsapi
import pandas as pd

app = Flask(__name__)

# 將全端網頁宣告為單一字串
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2026 MLB 數據深度分析與大谷翔平專區</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-light">

    <div class="container py-5">
        <h1 class="mb-2 text-center fw-bold text-primary">2026 MLB 數據深度分析看板</h1>
        <p class="text-muted text-center mb-5">全端單一 app.py 架構：Python (Pandas) 後端計算，前端 JS 實時動態渲染</p>

        <div class="row mb-5">
            <div class="col-12">
                <div class="card shadow-sm border-0">
                    <div class="card-header bg-primary text-white py-3">
                        <h3 class="card-title mb-0 fw-bold">🦄 大谷翔平 (Shohei Ohtani) 2026 進階數據分析專區</h3>
                    </div>
                    <div class="card-body p-4">
                        <div class="row align-items-center mb-4">
                            <div class="col-md-3 text-center border-end">
                                <h5 class="text-muted">傳統三圍 (AVG/OBP/SLG)</h5>
                                <h2 class="fw-bold text-dark" id="ohtaniSlash">-.--- / -.--- / -.---</h2>
                                <span class="badge bg-secondary fs-6" id="ohtaniHr">-- 全壘打</span>
                                <span class="badge bg-info text-dark fs-6 ms-2" id="ohtaniRbi">-- 打點</span>
                            </div>
                            <div class="col-md-9">
                                <h5 class="text-muted mb-3 fw-bold">Pandas 後端計算：進階打擊指標分析</h5>
                                <div class="row text-center">
                                    <div class="col-4 col-sm-2 mb-3">
                                        <div class="bg-light p-2 rounded">
                                            <div class="small text-muted">攻擊指數 (OPS)</div>
                                            <div class="fs-4 fw-bold text-primary" id="metricOps">-.---</div>
                                        </div>
                                    </div>
                                    <div class="col-4 col-sm-2 mb-3">
                                        <div class="bg-light p-2 rounded">
                                            <div class="small text-muted">純長打率 (ISO)</div>
                                            <div class="fs-4 fw-bold" id="metricIso">-.---</div>
                                        </div>
                                    </div>
                                    <div class="col-4 col-sm-2 mb-3">
                                        <div class="bg-light p-2 rounded">
                                            <div class="small text-muted">保送/三振比 (BB/K)</div>
                                            <div class="fs-4 fw-bold" id="metricBbk">-.---</div>
                                        </div>
                                    </div>
                                    <div class="col-4 col-sm-2 mb-3">
                                        <div class="bg-light p-2 rounded">
                                            <div class="small text-muted">全壘打率 (AB/HR)</div>
                                            <div class="fs-4 fw-bold" id="metricAbhr">--.-</div>
                                        </div>
                                    </div>
                                    <div class="col-4 col-sm-2 mb-3">
                                        <div class="bg-light p-2 rounded">
                                            <div class="small text-muted">打擊率/上壘率差</div>
                                            <div class="fs-4 fw-bold text-success" id="metricEye">-.---</div>
                                        </div>
                                    </div>
                                    <div class="col-4 col-sm-2 mb-3">
                                        <div class="bg-light p-2 rounded">
                                            <div class="small text-muted">出賽場次</div>
                                            <div class="fs-4 fw-bold" id="metricGames">--</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-4 mb-md-0">
                                <div class="border rounded p-3 bg-white">
                                    <h6 class="fw-bold text-muted mb-3">打擊型態指標視覺化</h6>
                                    <div style="position: relative; height:250px;">
                                        <canvas id="ohtaniRadarChart"></canvas>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="border rounded p-3 bg-white h-100">
                                    <h6 class="fw-bold text-muted mb-2">數據深度解讀</h6>
                                    <p class="text-dark small" id="ohtaniAnalysisText">
                                        正在分析數據中...
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card shadow-sm border-0 mb-4">
                    <div class="card-header bg-dark text-white py-3">
                        <h3 class="card-title mb-0 fw-bold">聯盟球隊期望勝率與運氣指數 (Luck Factor)</h3>
                    </div>
                    <div class="card-body p-4">
                        <div class="mb-4" style="position: relative; height:350px;">
                            <canvas id="mlbChart"></canvas>
                        </div>
                        <h4 class="mb-3 fw-bold">球隊深度數據表格</h4>
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
        </div>
    </div>

    <script>
        fetch('/api/analysis')
            .then(response => response.json())
            .then(res => {
                if(res.status === 'success') {
                    renderOhtaniSection(res.ohtani_analysis);
                    renderTeamSection(res.team_analysis);
                } else {
                    alert('資料載入失敗: ' + res.message);
                }
            });

        function renderOhtaniSection(ohtani) {
            document.getElementById('ohtaniSlash').innerText = `${ohtani.avg} / ${ohtani.obp} / ${ohtani.slg}`;
            document.getElementById('ohtaniHr').innerText = `${ohtani.home_runs} 全壘打`;
            document.getElementById('ohtaniRbi').innerText = `${ohtani.rbi} 打點`;
            
            document.getElementById('metricOps').innerText = ohtani.ops;
            document.getElementById('metricIso').innerText = ohtani.iso;
            document.getElementById('metricBbk').innerText = ohtani.bb_k_ratio;
            document.getElementById('metricAbhr').innerText = ohtani.ab_per_hr;
            document.getElementById('metricEye').innerText = ohtani.obp_avg_diff;
            document.getElementById('metricGames').innerText = ohtani.games_played;

            let interpretation = `大谷翔平在當前球季出賽 ${ohtani.games_played} 場，擊出 ${ohtani.home_runs} 支全壘打。`;
            interpretation += ` 在進階指標上，他的純長打率 (ISO) 為 <strong>${ohtani.iso}</strong>，`;
            if (parseFloat(ohtani.iso) >= 0.250) {
                interpretation += `這顯示出<strong>極為恐怖的菁英級長打火力和重擊球能力</strong>。`;
            } else {
                interpretation += `長打火力處於常態範圍的穩定發揮狀態。`;
            }
            
            interpretation += `<br/><br/>在選球與判斷指標方面，他的保送三振比 (BB/K) 為 <strong>${ohtani.bb_k_ratio}</strong>，打擊率與上壘率的差距 (OBP-AVG) 為 <strong>${ohtani.obp_avg_diff}</strong>。這代表他在追求極致長打的同時，`;
            if (parseFloat(ohtani.bb_k_ratio) > 0.6) {
                interpretation += `仍舊維持了非常優異的被動選球與高紀律保送率，能有效擴大對投手的威脅性。`;
            } else {
                interpretation += `目前的被三振率稍高，這是他全力揮棒、追求擊球初速與長打時常伴隨的盲點。`;
            }
            document.getElementById('ohtaniAnalysisText').innerHTML = interpretation;

            const ctx = document.getElementById('ohtaniRadarChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['打擊率 (AVG)', '上壘率 (OBP)', '長打率 (SLG)', '純長打率 (ISO)'],
                    datasets: [{
                        label: '打擊指標數值',
                        data: [parseFloat(ohtani.avg), parseFloat(ohtani.obp), parseFloat(ohtani.slg), parseFloat(ohtani.iso)],
                        backgroundColor: ['rgba(54, 162, 235, 0.6)', 'rgba(75, 192, 192, 0.6)', 'rgba(255, 99, 132, 0.6)', 'rgba(255, 159, 64, 0.6)'],
                        borderColor: ['rgba(54, 162, 235, 1)', 'rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)', 'rgba(255, 159, 64, 1)'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, max: 1.0 } }
                }
            });
        }

        function renderTeamSection(teams) {
            const tableBody = document.querySelector('#dataTable tbody');
            tableBody.innerHTML = ""; // 先清空舊資料
            const labels = [];
            const luckFactors = [];

            // 修正點：只抓前 15 名放進圖表，避免圖表爆掉擠在一起
            const displayTeams = teams.slice(0, 15);

            teams.forEach(team => {
                const luckVal = parseFloat(team.luck_factor) * 100;
                const row = `
                    <tr>
                        <td class="fw-bold">${team.team_name}</td>
                        <td>${team.division}</td>
                        <td>${team.w} - ${team.l}</td>
                        <td>${(parseFloat(team.actual_win_pct) * 100).toFixed(1)}%</td>
                        <td class="${luckVal >= 0 ? 'text-success' : 'text-danger'}">
                            ${luckVal >= 0 ? '+' : ''}${luckVal.toFixed(1)}%
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });

            displayTeams.forEach(team => {
                labels.push(team.team_name);
                luckFactors.push(parseFloat(team.luck_factor) * 100); // 轉換為百分比數值
            });

            const ctx = document.getElementById('mlbChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '運氣成分 % (正值代表實際戰績高於期望勝率)',
                        data: luckFactors,
                        backgroundColor: luckFactors.map(val => val >= 0 ? 'rgba(40, 167, 69, 0.6)' : 'rgba(220, 53, 69, 0.6)'),
                        borderColor: luckFactors.map(val => val >= 0 ? 'rgb(40, 167, 69)' : 'rgb(220, 53, 69)'),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { 
                        y: { 
                            ticks: {
                                callback: function(value) { return value + '%'; } // Y 軸加上 % 符號
                            }
                        } 
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return FRONTEND_HTML

@app.route('/api/analysis')
def get_mlb_analysis():
    try:
        # === 1. 大谷翔平 (ID: 660271) 數據抓取與 Pandas 深度分析 ===
        player_stats = statsapi.player_stat_data(660271, group="hitting", type="season", sportId=1)
        
        ohtani_processed = {
            "games_played": 0, "home_runs": 0, "rbi": 0,
            "avg": ".000", "obp": ".000", "slg": ".000", "ops": ".000",
            "iso": ".000", "bb_k_ratio": "0.00", "ab_per_hr": "0.0", "obp_avg_diff": ".000"
        }
        
        if player_stats and 'stats' in player_stats and len(player_stats['stats']) > 0:
            raw_stats = player_stats['stats'][0]['stats']
            s_series = pd.Series(raw_stats)
            
            ab = int(s_series.get('atBats', 0))
            hr = int(s_series.get('homeRuns', 0))
            bb = int(s_series.get('baseOnBalls', 0))
            so = int(s_series.get('strikeOuts', 0))
            
            avg_val = float(s_series.get('avg', 0.0))
            obp_val = float(s_series.get('obp', 0.0))
            slg_val = float(s_series.get('slg', 0.0))
            ops_val = float(s_series.get('ops', 0.0))
            
            iso_val = slg_val - avg_val                          
            bb_k = round(bb / so, 2) if so > 0 else bb           
            ab_hr = round(ab / hr, 1) if hr > 0 else 0.0         
            eye_diff = obp_val - avg_val                         

            ohtani_processed = {
                "games_played": int(s_series.get('gamesPlayed', 0)),
                "home_runs": hr,
                "rbi": int(s_series.get('rbi', 0)),
                "avg": f"{avg_val:.3f}",
                "obp": f"{obp_val:.3f}",
                "slg": f"{slg_val:.3f}",
                "ops": f"{ops_val:.3f}",
                "iso": f"{iso_val:.3f}",
                "bb_k_ratio": f"{bb_k:.2f}",
                "ab_per_hr": f"{ab_hr:.1f}",
                "obp_avg_diff": f"{eye_diff:.3f}"
            }

        # === 2. 聯盟球隊戰績期望值與運氣指數分析 (全面加上強制型態轉換) ===
        standings_data = statsapi.standings_data(leagueId="103,104", season=2026)
        raw_teams = []
        for div_id, div_info in standings_data.items():
            div_name = div_info['div_name']
            for team in div_info['teams']:
                raw_teams.append({
                    'division': div_name, 
                    'team_name': team['name'],
                    'w': int(team['w']), 
                    'l': int(team['l']),
                    'rs': float(team.get('rs', 0)), # 強制將得分轉為 float 確保 Pandas 平方計算正確
                    'ra': float(team.get('ra', 0))  # 強制將失分轉為 float
                })
        
        df_teams = pd.DataFrame(raw_teams)
        if not df_teams.empty and 'rs' in df_teams.columns and df_teams['rs'].sum() > 0:
            # 畢達哥拉斯期望勝率計算
            df_teams['expected_win_pct'] = (df_teams['rs']**2) / (df_teams['rs']**2 + df_teams['ra']**2)
            df_teams['actual_win_pct'] = df_teams['w'] / (df_teams['w'] + df_teams['l'])
            df_teams['luck_factor'] = df_teams['actual_win_pct'] - df_teams['expected_win_pct']
        else:
            df_teams['actual_win_pct'] = df_teams['w'] / (df_teams['w'] + df_teams['l']) if not df_teams.empty else 0
            df_teams['luck_factor'] = 0
            
        df_teams = df_teams.sort_values(by='actual_win_pct', ascending=False)
        team_list = df_teams.to_dict(orient='records')

        return jsonify({
            "status": "success",
            "ohtani_analysis": ohtani_processed,
            "team_analysis": team_list
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)