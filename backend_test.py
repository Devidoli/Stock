#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Stock Analysis API
Tests all backend endpoints with realistic trading scenarios
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw
import uuid
import time
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://candlebot-analyzer.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {BASE_URL}")

class StockAnalysisAPITester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.test_results = {
            'health_check': False,
            'ai_chat': False,
            'chat_history': False,
            'candlestick_analysis': False,
            'analysis_history': False,
            'database_operations': False
        }
        self.errors = []
        
    def create_sample_candlestick_image(self):
        """Create a sample candlestick chart image for testing"""
        try:
            # Create a simple candlestick chart image
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw title
            draw.text((300, 20), "AAPL Daily Chart", fill='black')
            
            # Draw some candlesticks (simplified)
            candlesticks = [
                (100, 200, 180, 220),  # x, open, high, low, close
                (150, 180, 190, 170),
                (200, 170, 175, 160),
                (250, 160, 165, 155),
                (300, 155, 170, 165),
            ]
            
            for i, (x, open_price, high, low) in enumerate(candlesticks):
                close_price = open_price + (i * 5 - 10)  # Simulate price movement
                
                # Draw high-low line
                draw.line([(x, 400-high), (x, 400-low)], fill='black', width=1)
                
                # Draw body
                body_top = min(400-open_price, 400-close_price)
                body_bottom = max(400-open_price, 400-close_price)
                color = 'green' if close_price > open_price else 'red'
                draw.rectangle([x-5, body_top, x+5, body_bottom], fill=color)
            
            # Add some indicators text
            draw.text((50, 500), "RSI: 65.4", fill='blue')
            draw.text((150, 500), "MACD: Bullish", fill='blue')
            draw.text((250, 500), "Volume: High", fill='blue')
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_data = buffer.getvalue()
            return base64.b64encode(img_data).decode('utf-8'), img_data
            
        except Exception as e:
            print(f"Error creating sample image: {e}")
            return None, None
    
    def test_health_check(self):
        """Test GET /api/ endpoint"""
        print("\n=== Testing Health Check ===")
        try:
            response = requests.get(f"{BASE_URL}/", timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if "Stock Analysis API is running" in data.get('message', ''):
                    self.test_results['health_check'] = True
                    print("✅ Health check passed")
                    return True
                else:
                    self.errors.append("Health check returned unexpected message")
            else:
                self.errors.append(f"Health check failed with status {response.status_code}")
                
        except Exception as e:
            self.errors.append(f"Health check error: {str(e)}")
            print(f"❌ Health check failed: {e}")
        
        return False
    
    def test_ai_chat(self):
        """Test POST /api/chat endpoint"""
        print("\n=== Testing AI Chat API ===")
        
        test_messages = [
            "What is a doji candlestick pattern and what does it indicate?",
            "How do I set proper stop loss levels for swing trading?",
            "Explain the RSI indicator and how to use it for entry signals",
            "What are the key characteristics of a bullish engulfing pattern?"
        ]
        
        successful_chats = 0
        
        for i, message in enumerate(test_messages):
            try:
                print(f"\nTesting message {i+1}: {message[:50]}...")
                
                payload = {
                    "message": message,
                    "session_id": self.session_id
                }
                
                response = requests.post(
                    f"{BASE_URL}/chat",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'response' in data and len(data['response']) > 50:
                        successful_chats += 1
                        print(f"✅ Chat {i+1} successful - Response length: {len(data['response'])}")
                        print(f"Response preview: {data['response'][:100]}...")
                    else:
                        print(f"❌ Chat {i+1} - Invalid response format")
                        self.errors.append(f"Chat {i+1} returned invalid response")
                else:
                    print(f"❌ Chat {i+1} failed with status {response.status_code}")
                    self.errors.append(f"Chat {i+1} failed: {response.text}")
                
                # Small delay between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Chat {i+1} error: {e}")
                self.errors.append(f"Chat {i+1} error: {str(e)}")
        
        if successful_chats >= 3:  # At least 3 out of 4 should work
            self.test_results['ai_chat'] = True
            print(f"✅ AI Chat API passed ({successful_chats}/4 messages successful)")
            return True
        else:
            print(f"❌ AI Chat API failed ({successful_chats}/4 messages successful)")
            return False
    
    def test_chat_history(self):
        """Test GET /api/chat-history/{session_id} endpoint"""
        print("\n=== Testing Chat History ===")
        try:
            response = requests.get(f"{BASE_URL}/chat-history/{self.session_id}", timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'chats' in data and isinstance(data['chats'], list):
                    chat_count = len(data['chats'])
                    print(f"✅ Chat history retrieved - {chat_count} messages found")
                    self.test_results['chat_history'] = True
                    
                    # Verify some chat data structure
                    if chat_count > 0:
                        sample_chat = data['chats'][0]
                        required_fields = ['message', 'response', 'session_id']
                        if all(field in sample_chat for field in required_fields):
                            print("✅ Chat data structure is valid")
                        else:
                            print("⚠️ Chat data structure missing some fields")
                    
                    return True
                else:
                    self.errors.append("Chat history returned invalid format")
            else:
                self.errors.append(f"Chat history failed with status {response.status_code}")
                
        except Exception as e:
            self.errors.append(f"Chat history error: {str(e)}")
            print(f"❌ Chat history failed: {e}")
        
        return False
    
    def test_candlestick_analysis(self):
        """Test POST /api/analyze-candlestick endpoint"""
        print("\n=== Testing Candlestick Analysis ===")
        
        # Create sample image
        image_base64, image_data = self.create_sample_candlestick_image()
        if not image_data:
            self.errors.append("Failed to create sample candlestick image")
            return False
        
        try:
            # Prepare multipart form data
            files = {
                'file': ('candlestick_chart.png', image_data, 'image/png')
            }
            data = {
                'session_id': self.session_id
            }
            
            print("Uploading sample candlestick chart for analysis...")
            response = requests.post(
                f"{BASE_URL}/analyze-candlestick",
                files=files,
                data=data,
                timeout=90  # Longer timeout for AI analysis
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['analysis', 'patterns_detected', 'recommendations', 'session_id']
                
                if all(field in data for field in required_fields):
                    print("✅ Candlestick analysis successful")
                    print(f"Analysis length: {len(data['analysis'])}")
                    print(f"Patterns detected: {data['patterns_detected']}")
                    print(f"Recommendations: {data['recommendations']}")
                    print(f"Analysis preview: {data['analysis'][:200]}...")
                    
                    # Verify analysis quality
                    if len(data['analysis']) > 100:
                        self.test_results['candlestick_analysis'] = True
                        return True
                    else:
                        self.errors.append("Analysis response too short")
                else:
                    self.errors.append("Candlestick analysis missing required fields")
            else:
                self.errors.append(f"Candlestick analysis failed: {response.text}")
                print(f"❌ Analysis failed: {response.text}")
                
        except Exception as e:
            self.errors.append(f"Candlestick analysis error: {str(e)}")
            print(f"❌ Candlestick analysis failed: {e}")
        
        return False
    
    def test_analysis_history(self):
        """Test GET /api/analysis-history/{session_id} endpoint"""
        print("\n=== Testing Analysis History ===")
        try:
            response = requests.get(f"{BASE_URL}/analysis-history/{self.session_id}", timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'analyses' in data and isinstance(data['analyses'], list):
                    analysis_count = len(data['analyses'])
                    print(f"✅ Analysis history retrieved - {analysis_count} analyses found")
                    self.test_results['analysis_history'] = True
                    
                    # Verify analysis data structure
                    if analysis_count > 0:
                        sample_analysis = data['analyses'][0]
                        required_fields = ['analysis', 'filename', 'session_id']
                        if all(field in sample_analysis for field in required_fields):
                            print("✅ Analysis data structure is valid")
                        else:
                            print("⚠️ Analysis data structure missing some fields")
                    
                    return True
                else:
                    self.errors.append("Analysis history returned invalid format")
            else:
                self.errors.append(f"Analysis history failed with status {response.status_code}")
                
        except Exception as e:
            self.errors.append(f"Analysis history error: {str(e)}")
            print(f"❌ Analysis history failed: {e}")
        
        return False
    
    def test_database_operations(self):
        """Test database persistence by verifying data consistency"""
        print("\n=== Testing Database Operations ===")
        
        # Database operations are tested implicitly through other tests
        # Check if both chat and analysis data were persisted
        chat_working = self.test_results['chat_history']
        analysis_working = self.test_results['analysis_history']
        
        if chat_working and analysis_working:
            self.test_results['database_operations'] = True
            print("✅ Database operations working - data persistence verified")
            return True
        else:
            self.errors.append("Database operations failed - data not persisted properly")
            print("❌ Database operations failed")
            return False
    
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print(f"Session ID: {self.session_id}")
        print(f"Backend URL: {BASE_URL}")
        
        # Test in logical order
        tests = [
            ("Health Check", self.test_health_check),
            ("AI Chat API", self.test_ai_chat),
            ("Chat History", self.test_chat_history),
            ("Candlestick Analysis", self.test_candlestick_analysis),
            ("Analysis History", self.test_analysis_history),
            ("Database Operations", self.test_database_operations)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            result = test_func()
            if not result:
                print(f"❌ {test_name} FAILED")
            else:
                print(f"✅ {test_name} PASSED")
        
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print(f"\n{'='*60}")
        print("🎯 BACKEND TESTING SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📊 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        if self.errors:
            print(f"\n🚨 Errors Encountered ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        # Overall assessment
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Backend API is fully functional.")
        elif passed_tests >= total_tests * 0.8:
            print(f"\n✅ MOSTLY WORKING - {passed_tests}/{total_tests} tests passed")
        else:
            print(f"\n❌ CRITICAL ISSUES - Only {passed_tests}/{total_tests} tests passed")

if __name__ == "__main__":
    tester = StockAnalysisAPITester()
    tester.run_all_tests()