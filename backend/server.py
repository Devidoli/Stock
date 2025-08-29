from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64
import shutil
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Ensure upload directory exists
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Define Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    message: str
    session_id: str

class CandlestickAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    filename: str
    analysis: str
    patterns_detected: List[str] = []
    indicators: dict = {}
    recommendations: dict = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper functions
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def prepare_from_mongo(data):
    """Convert MongoDB documents to JSON-serializable format"""
    if isinstance(data, list):
        return [prepare_from_mongo(item) for item in data]
    elif isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == '_id':
                result[key] = str(value)  # Convert ObjectId to string
            elif isinstance(value, dict):
                result[key] = prepare_from_mongo(value)
            elif isinstance(value, list):
                result[key] = prepare_from_mongo(value)
            else:
                result[key] = value
        return result
    else:
        return data

async def get_llm_chat(session_id: str, system_message: str = None):
    """Initialize LLM chat with session ID"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM API key not configured")
    
    if not system_message:
        system_message = """You are an expert stock market analyst and financial advisor specializing in candlestick pattern analysis and technical indicators. 

Your expertise includes:
- Candlestick pattern recognition (doji, hammer, shooting star, engulfing patterns, etc.)
- Technical indicators (RSI, MACD, Bollinger Bands, Moving Averages, etc.)
- Support and resistance levels
- Risk management (stop loss and profit booking strategies)
- Market sentiment analysis

Always provide:
1. Clear, actionable insights
2. Risk management recommendations
3. Entry/exit strategies when appropriate
4. Confidence levels for your analysis
5. Educational explanations for beginners

Keep responses professional yet accessible, and always emphasize risk management in trading."""

    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", "gpt-4o")
    
    return chat

async def analyze_candlestick_image(image_base64: str, session_id: str):
    """Analyze candlestick patterns from uploaded image using GPT-4V"""
    try:
        system_message = """You are an expert technical analyst specializing in candlestick pattern analysis. Analyze the uploaded candlestick chart image and provide:

1. **Pattern Recognition**: Identify specific candlestick patterns (doji, hammer, engulfing, etc.)
2. **Technical Indicators**: Analyze visible indicators (RSI, MACD, volume, moving averages)
3. **Support/Resistance**: Identify key levels
4. **Market Sentiment**: Current trend and momentum
5. **Trading Strategy**: 
   - Entry points
   - Stop loss levels (risk management)
   - Profit targets (profit booking levels)
   - Risk-reward ratio
6. **Confidence Level**: Rate your analysis confidence (1-10)

Be specific about timeframes, price levels, and provide actionable trading advice with proper risk management."""

        chat = await get_llm_chat(session_id, system_message)
        
        # Create message with image
        from emergentintegrations.llm.chat import ImageContent
        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text="Please analyze this candlestick chart image and provide comprehensive trading analysis with specific patterns, indicators, and trading recommendations including stop loss and profit booking strategies.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        logging.error(f"Error in candlestick analysis: {str(e)}")
        return f"Error analyzing image: {str(e)}"

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stock Analysis API is running"}

@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """Chat with AI for stock market advice and explanations"""
    try:
        chat = await get_llm_chat(request.session_id)
        user_message = UserMessage(text=request.message)
        response = await chat.send_message(user_message)
        
        # Save chat to database
        chat_data = ChatMessage(
            session_id=request.session_id,
            message=request.message,
            response=response
        )
        
        chat_dict = prepare_for_mongo(chat_data.dict())
        await db.chat_messages.insert_one(chat_dict)
        
        return {"response": response, "session_id": request.session_id}
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

@api_router.post("/analyze-candlestick")
async def analyze_candlestick_chart(
    file: UploadFile = File(...),
    session_id: str = "default"
):
    """Upload and analyze candlestick chart image"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and encode image
        file_content = await file.read()
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Analyze with AI
        analysis = await analyze_candlestick_image(image_base64, session_id)
        
        # Parse analysis for structured data (basic parsing - can be enhanced)
        patterns_detected = []
        indicators = {}
        recommendations = {}
        
        # Simple pattern detection in response
        pattern_keywords = ["doji", "hammer", "shooting star", "engulfing", "pin bar", "inside bar"]
        for pattern in pattern_keywords:
            if pattern.lower() in analysis.lower():
                patterns_detected.append(pattern.capitalize())
        
        # Extract basic recommendations
        if "stop loss" in analysis.lower():
            recommendations["risk_management"] = "Stop loss recommended"
        if "profit" in analysis.lower():
            recommendations["profit_booking"] = "Profit targets identified"
        if "buy" in analysis.lower():
            recommendations["action"] = "Potential buy signal"
        elif "sell" in analysis.lower():
            recommendations["action"] = "Potential sell signal"
        
        # Save analysis to database
        analysis_data = CandlestickAnalysis(
            session_id=session_id,
            filename=file.filename,
            analysis=analysis,
            patterns_detected=patterns_detected,
            indicators=indicators,
            recommendations=recommendations
        )
        
        analysis_dict = prepare_for_mongo(analysis_data.dict())
        await db.candlestick_analyses.insert_one(analysis_dict)
        
        return {
            "analysis": analysis,
            "patterns_detected": patterns_detected,
            "recommendations": recommendations,
            "session_id": session_id,
            "filename": file.filename
        }
        
    except Exception as e:
        logging.error(f"Candlestick analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        chats = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(100)
        return {"chats": chats, "session_id": session_id}
    except Exception as e:
        logging.error(f"Error fetching chat history: {str(e)}")
        return {"chats": [], "session_id": session_id}

@api_router.get("/analysis-history/{session_id}")
async def get_analysis_history(session_id: str):
    """Get analysis history for a session"""
    try:
        analyses = await db.candlestick_analyses.find({"session_id": session_id}).sort("timestamp", -1).to_list(50)
        return {"analyses": analyses, "session_id": session_id}
    except Exception as e:
        logging.error(f"Error fetching analysis history: {str(e)}")
        return {"analyses": [], "session_id": session_id}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()