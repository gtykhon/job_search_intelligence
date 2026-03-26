# 🤖 AI Provider Quick Reference

## Available AI Providers

| Provider | Setup Difficulty | Privacy | Cost | Performance |
|----------|------------------|---------|------|-------------|
| **Claude** | Easy | ⚠️ Cloud | 💰 Pay-per-use | ⭐⭐⭐⭐⭐ |
| **OpenAI** | Easy | ⚠️ Cloud | 💰 Pay-per-use | ⭐⭐⭐⭐⭐ |
| **Ollama** | Easy | ✅ Private | 🆓 Free | ⭐⭐⭐⭐ |
| **Llama.cpp** | Medium | ✅ Private | 🆓 Free | ⭐⭐⭐⭐⭐ |
| **Custom Local** | Hard | ✅ Private | 🆓 Free | ⭐⭐⭐ |

## Quick Setup Commands

### 🔥 Ollama (Recommended for Local)
```bash
# 1. Install Ollama from https://ollama.ai
# 2. Pull a model
ollama pull llama3.1:8b

# 3. Configure .env
AI_PROVIDER=ollama
AI_ENABLED=true
OLLAMA_MODEL=llama3.1:8b
```

### 🚀 Claude (Cloud)
```bash
# 1. Get API key from https://console.anthropic.com/
# 2. Configure .env
AI_PROVIDER=claude
AI_ENABLED=true
ANTHROPIC_API_KEY=your-api-key
```

### 🧠 OpenAI (Cloud)
```bash
# 1. Get API key from https://platform.openai.com/
# 2. Configure .env
AI_PROVIDER=openai
AI_ENABLED=true
OPENAI_API_KEY=your-api-key
```

### ⚡ Llama.cpp (Advanced)
```bash
# 1. Download a GGUF model
# 2. Configure .env
AI_PROVIDER=llamacpp
AI_ENABLED=true
LLAMACPP_MODEL_PATH=/path/to/model.gguf
```

## Model Recommendations

### Lightweight (2-4GB RAM)
- `llama3.1:3b` - Fast, good quality
- `phi3:mini` - Microsoft Phi-3, efficient

### Standard (8-16GB RAM) 
- `llama3.1:8b` - ⭐ **Recommended**
- `mistral:7b` - Good alternative

### Heavy (32GB+ RAM)
- `llama3.1:70b` - Best quality
- `mixtral:8x7b` - Mixture of experts

## Testing Your Setup

```bash
# Check configuration
python main.py --config-check

# Test AI analysis
python main.py --mode quick --ai-analysis

# Full intelligence test
python main.py --mode intelligence --ai-analysis
```

## Troubleshooting

### Ollama Not Working
```bash
# Check service
ollama serve

# List models  
ollama list

# Test model
ollama run llama3.1:8b "Hello"
```

### Performance Issues
- Use smaller models for limited RAM
- Increase GPU layers for GPU acceleration
- Reduce context size for faster responses

### Privacy Comparison

| Feature | Cloud AI | Local AI |
|---------|----------|----------|
| Data leaves your machine | ❌ Yes | ✅ No |
| Internet required | ❌ Yes | ✅ No |
| API costs | ❌ Yes | ✅ No |
| Setup complexity | ✅ Easy | ⚠️ Medium |
| Performance | ✅ Excellent | ✅ Good |

Choose local AI for maximum privacy! 🔐
