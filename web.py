import sqlite3
import json
import os
import asyncio
import subprocess
import re
import sys
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(title="ESET KeyGen Web API")

DB_PATH = "web_data.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preferences TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            license_name TEXT,
            license_key TEXT,
            expiration_date TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM config")
    if cursor.fetchone()[0] == 0:
        default_config = {
            "mode": "key",
            "email_api": "emailfake",
            "browser": "auto",
            "no_headless": False,
            "skip_update_check": False,
            "custom_email_api": False
        }
        cursor.execute("INSERT INTO config (preferences) VALUES (?)", (json.dumps(default_config),))
        
    conn.commit()
    conn.close()

init_db()

class ConfigModel(BaseModel):
    mode: str
    email_api: str
    browser: str
    no_headless: bool
    skip_update_check: bool
    custom_email_api: bool

def get_config() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT preferences FROM config ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return {}

def save_config(config_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE config SET preferences = ? WHERE id = (SELECT MAX(id) FROM config)", (json.dumps(config_data),))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO config (preferences) VALUES (?)", (json.dumps(config_data),))
    conn.commit()
    conn.close()

def save_history(email: str, password: str, license_name: Optional[str] = None, license_key: Optional[str] = None, expiration: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO history (timestamp, email, password, license_name, license_key, expiration_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (now, email, password, license_name, license_key, expiration))
    conn.commit()
    conn.close()

def get_history() -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

# Active subprocess reference
current_process = None
process_lock = asyncio.Lock()
active_websockets: List[WebSocket] = []

@app.get("/api/config")
async def api_get_config():
    return get_config()

@app.post("/api/config")
async def api_save_config(config: ConfigModel):
    save_config(config.dict())
    return {"status": "success"}

@app.get("/api/history")
async def api_get_history():
    return get_history()

def build_cli_args(config: ConfigModel) -> List[str]:
    args = [sys.executable, "main.py"]
    
    # Mode
    if config.mode == "key":
        args.append("--key")
    elif config.mode == "small_business_key":
        args.append("--small-business-key")
    elif config.mode == "advanced_key":
        args.append("--advanced-key")
    elif config.mode == "vpn_codes":
        args.append("--vpn-codes")
    elif config.mode == "account":
        args.append("--account")
    elif config.mode == "protecthub_account":
        args.append("--protecthub-account")
        
    # Email API
    if config.email_api:
        args.extend(["--email-api", config.email_api])
        
    # Browser
    if config.browser == "auto":
        args.append("--auto-detect-browser")
    elif config.browser == "chrome":
        args.append("--chrome")
    elif config.browser == "firefox":
        args.append("--firefox")
    elif config.browser == "edge":
        args.append("--edge")
        
    # Flags
    if config.no_headless:
        args.append("--no-headless")
    if config.skip_update_check:
        args.append("--skip-update-check")
    if config.custom_email_api:
        args.append("--custom-email-api")
        
    # Always disable logging to file when running from web UI to keep it clean,
    # or just let it log. We will capture stdout/stderr.
    args.append("--disable-progress-bar") # Better for text output parsing
    
    return args

@app.post("/api/generate")
async def api_generate(config: ConfigModel):
    global current_process
    
    async with process_lock:
        if current_process and current_process.poll() is None:
            raise HTTPException(status_code=400, detail="A generation process is already running.")
            
        save_config(config.dict())
        
        args = build_cli_args(config)
        try:
            # Use subprocess.Popen with pipes
            current_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1, # Line buffered
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Start background task to read output and broadcast
            asyncio.create_task(stream_output_and_parse(current_process))
            
            return {"status": "started", "pid": current_process.pid}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def api_stop():
    global current_process
    
    async with process_lock:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            # Give it a chance to terminate gracefully
            try:
                current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                current_process.kill()
            return {"status": "stopped"}
        return {"status": "not_running"}

async def broadcast_log(message: str):
    disconnected = []
    for ws in active_websockets:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
            
    for ws in disconnected:
        if ws in active_websockets:
            active_websockets.remove(ws)

async def stream_output_and_parse(process: subprocess.Popen):
    """Reads stdout from the process, broadcasts it, and parses final output for the DB."""
    
    # Regex patterns for parsing output
    # Example format:
    # Account Email: test@emailfake.com
    # Account Password: password123
    # License Name: ESET HOME
    # License Key: XXXX-XXXX-XXXX-XXXX
    email_pattern = re.compile(r'Account Email\s*:\s*([^\s]+)')
    password_pattern = re.compile(r'Account Password\s*:\s*([^\s]+)')
    name_pattern = re.compile(r'License Name\s*:\s*(.+)')
    key_pattern = re.compile(r'License Key\s*:\s*([^\s]+)')
    
    email = None
    password = None
    license_name = None
    license_key = None
    
    try:
        # Read lines asynchronously (using asyncio.to_thread since process.stdout.readline blocks)
        while True:
            line = await asyncio.to_thread(process.stdout.readline)
            if not line and process.poll() is not None:
                break
                
            if line:
                line_str = line.strip()
                await broadcast_log(line_str)
                
                # Parse data
                if match := email_pattern.search(line_str):
                    email = match.group(1)
                elif match := password_pattern.search(line_str):
                    password = match.group(1)
                elif match := name_pattern.search(line_str):
                    license_name = match.group(1).strip()
                elif match := key_pattern.search(line_str):
                    license_key = match.group(1)

        # Process ended
        return_code = process.poll()
        await broadcast_log(f"[SYSTEM] Process finished with exit code {return_code}")
        
        # Save to DB if we got at least an email and password
        if email and password:
            save_history(email, password, license_name, license_key)
            await broadcast_log("[SYSTEM] Saved generated credentials to history database.")
            
    except Exception as e:
        await broadcast_log(f"[SYSTEM ERROR] {str(e)}")

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        # Keep connection open
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# Mount static files at the end to not shadow API routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web:app", host="0.0.0.0", port=8000, reload=True)

