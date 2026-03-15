import asyncio
import json
import os
import time
import threading
from datetime import datetime
from aiohttp import web
import aiohttp
from road_ai import analyze_road_conditions

# File to persist potholes
DATA_FILE = 'potholes_data.json'

def load_potholes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_potholes(potholes):
    with open(DATA_FILE, 'w') as f:
        json.dump(potholes, f, indent=2)

# Load existing potholes on startup
potholes = load_potholes()
print(f"Loaded {len(potholes)} existing potholes from database")

latest_data = {}
latest_report = {
    "summary": "Waiting for pothole data...",
    "severity_assessment": "",
    "likely_cause": "",
    "recommendation": "",
    "priority": "LOW",
    "estimated_repair_cost": "N/A"
}
is_analyzing = False
last_report_time = 0

def run_ai_report():
    global latest_report, is_analyzing, last_report_time
    is_analyzing = True
    try:
        result = analyze_road_conditions(potholes)
        latest_report = result
        print(f"AI Report: {result['priority']} | {result['estimated_repair_cost']}")
    except Exception as e:
        print(f"AI error: {e}")
    is_analyzing = False
    last_report_time = time.time()

async def handle_websocket(request):
    global latest_data
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Device connected!")

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                latest_data = data

                if data.get('is_pothole') and data.get('gps', {}).get('lat'):
                    pothole = {
                        "id": len(potholes) + 1,
                        "lat": data['gps']['lat'],
                        "lng": data['gps']['lng'],
                        "impact": data['impact'],
                        "timestamp": datetime.now().isoformat(),
                        "severity": get_severity(data['impact']),
                        "reported": False
                    }
                    potholes.append(pothole)
                    save_potholes(potholes)
                    print(f"Pothole #{len(potholes)} saved! Impact: {data['impact']} [{pothole['severity']}]")

                    if len(potholes) % 3 == 0 and not is_analyzing:
                        thread = threading.Thread(target=run_ai_report)
                        thread.daemon = True
                        thread.start()

            except Exception as e:
                print(f"Data error: {e}")

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print(f"WebSocket error: {ws.exception()}")

    print("Device disconnected")
    return ws

def get_severity(impact):
    if impact > 8:
        return "HIGH"
    elif impact > 5:
        return "MEDIUM"
    else:
        return "LOW"

async def handle_file(request):
    filename = request.match_info.get('filename', 'road_dashboard.html')
    filepath = os.path.join('/Users/rohit/InjuryIQ', filename)
    if os.path.exists(filepath):
        return web.FileResponse(filepath)
    return web.Response(text="File not found", status=404)

async def handle_potholes_api(request):
    return web.json_response({
        "potholes": potholes,
        "total": len(potholes)
    })

async def handle_report_api(request):
    return web.json_response({
        "report": latest_report,
        "total_potholes": len(potholes),
        "is_analyzing": is_analyzing
    })

async def handle_government_report_api(request):
    high = [p for p in potholes if p['severity'] == 'HIGH']
    medium = [p for p in potholes if p['severity'] == 'MEDIUM']
    low = [p for p in potholes if p['severity'] == 'LOW']

    report = {
        "report_title": "RoadSense Pothole Detection Report",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_potholes": len(potholes),
            "high_severity": len(high),
            "medium_severity": len(medium),
            "low_severity": len(low),
            "estimated_repair_cost": latest_report.get("estimated_repair_cost", "N/A"),
            "priority": latest_report.get("priority", "N/A")
        },
        "ai_analysis": latest_report,
        "potholes": potholes,
        "recommendations": latest_report.get("recommendation", ""),
        "likely_cause": latest_report.get("likely_cause", "")
    }
    return web.json_response(report)

async def handle_clear_api(request):
    potholes.clear()
    save_potholes(potholes)
    return web.json_response({"status": "cleared"})

@web.middleware
async def cors_middleware(request, handler):
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

app = web.Application(middlewares=[cors_middleware])
app.router.add_get('/ws', handle_websocket)
app.router.add_get('/api/potholes', handle_potholes_api)
app.router.add_get('/api/report', handle_report_api)
app.router.add_get('/api/government_report', handle_government_report_api)
app.router.add_get('/api/clear', handle_clear_api)
app.router.add_get('/{filename}', handle_file)
app.router.add_get('/', handle_file)

if __name__ == '__main__':
    print("RoadSense server starting on port 8083")
    print(f"Dashboard: http://localhost:8083/road_dashboard.html")
    web.run_app(app, port=8083)