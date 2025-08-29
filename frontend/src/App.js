import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Generate unique session ID
const generateSessionId = () => {
  return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
};

function App() {
  const [sessionId] = useState(() => generateSessionId());
  const [activeTab, setActiveTab] = useState('analyze');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

  // Auto scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Load chat history on mount
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat-history/${sessionId}`);
      if (response.data.chats) {
        setChatMessages(response.data.chats);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const response = await axios.post(`${API}/analyze-candlestick`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setAnalysisResult(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      setAnalysisResult({
        error: 'Failed to analyze image. Please try again.',
        analysis: 'Error: ' + (error.response?.data?.detail || error.message)
      });
    } finally {
      setIsUploading(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || isChatting) return;

    const userMessage = { message: chatInput, sender: 'user', timestamp: new Date() };
    setChatMessages(prev => [...prev, userMessage]);
    setIsChatting(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: chatInput,
        session_id: sessionId
      });

      const aiMessage = { 
        message: response.data.response, 
        sender: 'ai', 
        timestamp: new Date() 
      };
      setChatMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { 
        message: 'Sorry, I encountered an error. Please try again.', 
        sender: 'ai', 
        timestamp: new Date() 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatInput('');
      setIsChatting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-20"
          style={{
            backgroundImage: 'url("https://images.unsplash.com/photo-1611091421107-f3ff17e327ff?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwzfHxzdG9jayUyMG1hcmtldHxlbnwwfHx8Ymx1ZXwxNzU2NDY5NDI4fDA&ixlib=rb-4.1.0&q=85")'
          }}
        />
        <div className="relative z-10 container mx-auto px-6 py-20">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                CandleBot
              </span>
              <br />
              <span className="text-4xl md:text-5xl">Analyzer</span>
            </h1>
            <p className="text-xl md:text-2xl text-blue-200 mb-8 max-w-3xl mx-auto leading-relaxed">
              AI-Powered Candlestick Pattern Analysis with Advanced Technical Indicators
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={() => setActiveTab('analyze')}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-semibold text-lg hover:shadow-xl hover:scale-105 transform transition-all duration-300"
              >
                Analyze Charts
              </button>
              <button 
                onClick={() => setActiveTab('chat')}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold text-lg hover:shadow-xl hover:scale-105 transform transition-all duration-300"
              >
                AI Trading Assistant
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="container mx-auto px-6 py-8">
        <div className="flex justify-center mb-8">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-2 border border-slate-700">
            <button
              onClick={() => setActiveTab('analyze')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                activeTab === 'analyze'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              📈 Chart Analysis
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 ml-2 ${
                activeTab === 'chat'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              🤖 AI Assistant
            </button>
          </div>
        </div>

        {/* Chart Analysis Tab */}
        {activeTab === 'analyze' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-slate-800/60 backdrop-blur-sm rounded-3xl p-8 border border-slate-700 shadow-2xl">
              <h2 className="text-3xl font-bold text-white mb-6 text-center">
                Upload Candlestick Chart for Analysis
              </h2>
              
              {/* Upload Area */}
              <div 
                className="border-2 border-dashed border-blue-500/50 rounded-2xl p-12 text-center hover:border-blue-400 transition-colors cursor-pointer bg-slate-900/30"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="text-6xl mb-4">📊</div>
                <p className="text-xl text-blue-200 mb-4">
                  {isUploading ? 'Analyzing your chart...' : 'Click to upload or drag & drop your candlestick chart'}
                </p>
                <p className="text-sm text-slate-400">
                  Supports PNG, JPG, JPEG formats
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>

              {/* Analysis Results */}
              {analysisResult && (
                <div className="mt-8">
                  <div className="bg-slate-900/50 rounded-2xl p-6 border border-slate-600">
                    <h3 className="text-2xl font-bold text-white mb-4 flex items-center">
                      <span className="text-2xl mr-3">🔍</span>
                      Analysis Results
                    </h3>
                    
                    {analysisResult.error ? (
                      <div className="text-red-400 bg-red-900/20 p-4 rounded-xl border border-red-600">
                        {analysisResult.analysis}
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Patterns Detected */}
                        {analysisResult.patterns_detected?.length > 0 && (
                          <div className="bg-blue-900/20 p-4 rounded-xl border border-blue-600">
                            <h4 className="font-semibold text-blue-300 mb-2">🎯 Patterns Detected:</h4>
                            <div className="flex flex-wrap gap-2">
                              {analysisResult.patterns_detected.map((pattern, index) => (
                                <span key={index} className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
                                  {pattern}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recommendations */}
                        {Object.keys(analysisResult.recommendations || {}).length > 0 && (
                          <div className="bg-green-900/20 p-4 rounded-xl border border-green-600">
                            <h4 className="font-semibold text-green-300 mb-2">💡 Recommendations:</h4>
                            {Object.entries(analysisResult.recommendations).map(([key, value]) => (
                              <div key={key} className="text-sm text-green-200">
                                <strong>{key.replace('_', ' ').toUpperCase()}:</strong> {value}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Full Analysis */}
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-600">
                          <h4 className="font-semibold text-slate-200 mb-3">📋 Detailed Analysis:</h4>
                          <div className="text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">
                            {analysisResult.analysis}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Chat Tab */}
        {activeTab === 'chat' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-slate-800/60 backdrop-blur-sm rounded-3xl border border-slate-700 shadow-2xl overflow-hidden">
              <div className="p-6 bg-gradient-to-r from-purple-600 to-pink-600">
                <h2 className="text-3xl font-bold text-white text-center">
                  🤖 AI Trading Assistant
                </h2>
                <p className="text-center text-purple-100 mt-2">
                  Ask me about trading strategies, market analysis, or any financial questions
                </p>
              </div>
              
              {/* Chat Messages */}
              <div className="h-96 overflow-y-auto p-6 bg-slate-900/20">
                {chatMessages.length === 0 ? (
                  <div className="text-center text-slate-400 py-8">
                    <div className="text-4xl mb-4">💬</div>
                    <p>Start a conversation with your AI trading assistant!</p>
                    <div className="mt-4 text-sm space-y-1">
                      <p>• Ask about candlestick patterns</p>
                      <p>• Get trading advice</p>
                      <p>• Learn about technical indicators</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chatMessages.map((msg, index) => (
                      <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs md:max-w-md p-4 rounded-2xl ${
                          msg.sender === 'user' 
                            ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white' 
                            : 'bg-slate-800 text-slate-200 border border-slate-600'
                        }`}>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.message}</p>
                          <p className="text-xs opacity-70 mt-2">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="p-6 bg-slate-800/50 border-t border-slate-700">
                <div className="flex gap-3">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me about trading, candlestick patterns, or market analysis..."
                    className="flex-1 bg-slate-900/50 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 resize-none"
                    rows="2"
                    disabled={isChatting}
                  />
                  <button
                    onClick={sendChatMessage}
                    disabled={!chatInput.trim() || isChatting}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all duration-300"
                  >
                    {isChatting ? '...' : 'Send'}
                  </button>
                </div>
                <p className="text-xs text-slate-500 mt-2">Press Enter to send, Shift+Enter for new line</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Feature Section */}
      <div className="py-16 bg-slate-900/50">
        <div className="container mx-auto px-6">
          <h2 className="text-4xl font-bold text-center text-white mb-12">
            Powerful Trading Analysis Features
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-slate-800/60 backdrop-blur-sm p-6 rounded-2xl border border-slate-700 text-center hover:transform hover:scale-105 transition-all duration-300">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-bold text-white mb-3">Pattern Recognition</h3>
              <p className="text-slate-300">Advanced AI identifies candlestick patterns with high accuracy including doji, hammers, and engulfing patterns.</p>
            </div>
            <div className="bg-slate-800/60 backdrop-blur-sm p-6 rounded-2xl border border-slate-700 text-center hover:transform hover:scale-105 transition-all duration-300">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-bold text-white mb-3">Technical Indicators</h3>
              <p className="text-slate-300">Analyze RSI, MACD, Bollinger Bands, and more to make informed trading decisions.</p>
            </div>
            <div className="bg-slate-800/60 backdrop-blur-sm p-6 rounded-2xl border border-slate-700 text-center hover:transform hover:scale-105 transition-all duration-300">
              <div className="text-4xl mb-4">🛡️</div>
              <h3 className="text-xl font-bold text-white mb-3">Risk Management</h3>
              <p className="text-slate-300">Get precise stop-loss and profit-booking recommendations to protect your investments.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-slate-900 py-8 border-t border-slate-700">
        <div className="container mx-auto px-6 text-center">
          <p className="text-slate-400">
            CandleBot Analyzer - Professional Trading Analysis Powered by AI
          </p>
          <p className="text-slate-500 text-sm mt-2">
            ⚠️ Trading involves risk. Always do your own research and consider consulting with a financial advisor.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;