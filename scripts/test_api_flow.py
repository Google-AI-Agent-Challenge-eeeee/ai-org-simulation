"""전체 API 흐름 검증 스크립트."""
import urllib.request, json

BASE = "http://localhost:8000"

def post(url, data=b"{}"):
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req).read())

def get(url):
    return json.loads(urllib.request.urlopen(url).read())

# 1. 세션 생성
sid = post(f"{BASE}/api/sessions")["session_id"]
print(f"[1] session_id: {sid}")

# 2. 요구사항
req = get(f"{BASE}/api/sessions/{sid}/requirements")
print(f"[2] project: {req['project_name']} | features: {len(req['features'])}개")

# 3. 요구사항 수락
post(f"{BASE}/api/sessions/{sid}/requirements/accept")
print(f"[3] requirements accepted")

# 4. 팀 목록
teams = get(f"{BASE}/api/sessions/{sid}/teams")
print(f"[4] teams: {teams['totalCombinations']}개 조합 | 추천: {teams['teams'][0]['team_name']}")

# 5. 팀 선택
post(f"{BASE}/api/sessions/{sid}/teams/select", data=json.dumps({"teamId": "team_001"}).encode())
print(f"[5] team selected")

# 6. 리포트
report = get(f"{BASE}/api/sessions/{sid}/report")
print(f"[6] report teamFitScore: {report['metrics']['teamFitScore']} | riskLevel: {report['metrics']['riskLevel']}")

print("\n✅ 전체 API 흐름 정상")
