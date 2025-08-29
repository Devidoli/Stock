#!/usr/bin/env python3
"""
Final Backend Verification - Test complete flow with analysis history
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
    """Create a sample candlestick chart"""
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((200, 20), "TSLA 1H Chart", fill='black')
    
    # Draw candlesticks
    for i in range(5):
        x = 100 + i * 80
        draw.line([(x, 150), (x, 250)], fill='black', width=2)
        draw.rectangle([x-10, 180, x+10, 220], fill='green' if i % 2 else 'red')
    
    draw.text((50, 350), "Strong bullish momentum with doji pattern", fill='blue')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_complete_flow():
    session_id = str(uuid.uuid4())
    print(f"Testing complete flow with session: {session_id}")
    
    # 1. Upload and analyze image
    print("\n1. Testing image analysis...")
    image_data = create_sample_image()
    files = {'file': ('test_chart.png', image_data, 'image/png')}
    data = {'session_id': session_id}
    
    response = requests.post(f"{BASE_URL}/analyze-candlestick", files=files, data=data, timeout=60)
    if response.status_code == 200:
        print("✅ Image analysis successful")
        analysis_result = response.json()
        print(f"Analysis preview: {analysis_result['analysis'][:100]}...")
    else:
        print(f"❌ Image analysis failed: {response.status_code}")
        return False
    
    # 2. Check analysis history
    print("\n2. Testing analysis history retrieval...")
    response = requests.get(f"{BASE_URL}/analysis-history/{session_id}")
    if response.status_code == 200:
        history = response.json()
        analysis_count = len(history['analyses'])
        print(f"✅ Analysis history retrieved: {analysis_count} analyses found")
        if analysis_count > 0:
            print("✅ Analysis persistence verified")
        else:
            print("⚠️ No analyses found in history")
    else:
        print(f"❌ Analysis history failed: {response.status_code}")
        return False
    
    # 3. Test chat functionality
    print("\n3. Testing AI chat...")
    chat_payload = {
        "message": "Based on my recent chart analysis, what should be my next trading move?",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_payload, timeout=60)
    if response.status_code == 200:
        chat_result = response.json()
        print("✅ AI chat successful")
        print(f"Response preview: {chat_result['response'][:100]}...")
    else:
        print(f"❌ AI chat failed: {response.status_code}")
        return False
    
    # 4. Check chat history
    print("\n4. Testing chat history retrieval...")
    response = requests.get(f"{BASE_URL}/chat-history/{session_id}")
    if response.status_code == 200:
        history = response.json()
        chat_count = len(history['chats'])
        print(f"✅ Chat history retrieved: {chat_count} messages found")
        if chat_count > 0:
            print("✅ Chat persistence verified")
        else:
            print("⚠️ No chats found in history")
    else:
        print(f"❌ Chat history failed: {response.status_code}")
        return False
    
    print("\n🎉 Complete flow verification PASSED!")
    return True

if __name__ == "__main__":
    test_complete_flow()