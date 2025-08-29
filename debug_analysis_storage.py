#!/usr/bin/env python3
"""
Debug analysis storage to verify MongoDB persistence
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw
import uuid
import time
import os
from dotenv import load_dotenv

load_dotenv('/app/frontend/.env')
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://candlebot-analyzer.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

def create_sample_image():
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((150, 20), "DEBUG TEST", fill='black')
    draw.rectangle([100, 100, 300, 200], fill='red')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def debug_analysis_flow():
    session_id = f"debug_session_{int(time.time())}"
    print(f"Debug session: {session_id}")
    
    # Upload analysis
    print("\n1. Uploading analysis...")
    image_data = create_sample_image()
    files = {'file': ('debug_chart.png', image_data, 'image/png')}
    data = {'session_id': session_id}
    
    response = requests.post(f"{BASE_URL}/analyze-candlestick", files=files, data=data, timeout=60)
    print(f"Upload status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Analysis ID in response: {result.get('session_id')}")
        print(f"Filename: {result.get('filename')}")
    
    # Wait a moment for database write
    print("\n2. Waiting for database write...")
    time.sleep(3)
    
    # Check history immediately
    print("\n3. Checking analysis history...")
    response = requests.get(f"{BASE_URL}/analysis-history/{session_id}")
    print(f"History status: {response.status_code}")
    if response.status_code == 200:
        history = response.json()
        print(f"Analyses found: {len(history['analyses'])}")
        if history['analyses']:
            for i, analysis in enumerate(history['analyses']):
                print(f"  Analysis {i+1}: {analysis.get('filename', 'No filename')}")
                print(f"    Session: {analysis.get('session_id', 'No session')}")
                print(f"    ID: {analysis.get('id', 'No ID')}")
    
    # Try with a different session to see all analyses
    print("\n4. Checking all recent analyses...")
    response = requests.get(f"{BASE_URL}/analysis-history/any_session")
    if response.status_code == 200:
        history = response.json()
        print(f"Total analyses in system: {len(history['analyses'])}")

if __name__ == "__main__":
    debug_analysis_flow()