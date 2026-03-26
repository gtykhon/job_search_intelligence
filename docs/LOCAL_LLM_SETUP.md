# Local LLM Setup Guide for Job Search Intelligence

## 🤖 Local LLM Integration Options

Your Job Search Intelligence now supports multiple local LLM options for privacy-focused AI analysis without sending data to external services.

## 🚀 Quick Setup Options

### Option 1: Ollama (Recommended - Easiest)

Ollama is the easiest way to run local LLMs with a simple setup process.

#### Installation:
1. **Download Ollama**: Visit [https://ollama.ai](https://ollama.ai) and download for your OS
2. **Install**: Follow the installer for your platform
3. **Pull a model**: Open terminal and run:
   ```bash
   ollama pull llama3.1:8b
   # or for a smaller model:
   ollama pull llama3.1:3b
   # or for a larger model (if you have enough RAM/VRAM):
   ollama pull llama3.1:70b
   ```

#### Configuration:
Edit your `.env` file:
```env
AI_ENABLED=true
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
AI_INSIGHTS=true
```

#### Usage:
```bash
# Start Ollama service (usually starts automatically)
ollama serve

# Test your Job Search Intelligence
python main.py --mode intelligence --ai-analysis
```

### Option 2: Llama.cpp (Advanced Users)

Direct model loading with llama.cpp for maximum control and performance.

#### Installation:
```bash
pip install llama-cpp-python
```

#### Model Setup:
1. **Download a GGUF model**: Visit [Hugging Face](https://huggingface.co/models?library=gguf)
2. **Recommended models**:
   - `microsoft/Phi-3-mini-4k-instruct-gguf` (3.8B parameters, ~2GB)
   - `meta-llama/Llama-2-7b-chat-gguf` (7B parameters, ~4GB)
   - `microsoft/Phi-3-medium-4k-instruct-gguf` (14B parameters, ~8GB)

3. **Download example**:
   ```bash
   # Create models directory
   mkdir -p models
   cd models
   
   # Download a model (example)
   wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
   ```

#### Configuration:
Edit your `.env` file:
```env
AI_ENABLED=true
AI_PROVIDER=llamacpp
LLAMACPP_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
LLAMACPP_N_CTX=4096
LLAMACPP_N_THREADS=4
LOCAL_GPU_LAYERS=0
AI_INSIGHTS=true
```

#### GPU Acceleration (Optional):
If you have a compatible GPU:
```env
LOCAL_GPU_LAYERS=20  # Adjust based on your GPU memory
```

### Option 3: Custom Local Model

For advanced users who want to integrate other local LLM frameworks.

#### Configuration:
```env
AI_ENABLED=true
AI_PROVIDER=local
LOCAL_MODEL_PATH=/path/to/your/model
AI_INSIGHTS=true
```

## 📊 Performance Comparison

| Option | Ease of Setup | Performance | Memory Usage | Privacy |
|--------|---------------|-------------|--------------|---------|
| Ollama | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Llama.cpp | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Custom | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🔧 Model Recommendations by Use Case

### Lightweight Analysis (2-4GB RAM)
- **Ollama**: `llama3.1:3b` or `phi3:mini`
- **Llama.cpp**: Phi-3-mini models

### Standard Analysis (8-16GB RAM)
- **Ollama**: `llama3.1:8b` or `llama3.1:7b-instruct`
- **Llama.cpp**: Llama-2-7b or Phi-3-medium models

### Advanced Analysis (32GB+ RAM)
- **Ollama**: `llama3.1:70b` or `mixtral:8x7b`
- **Llama.cpp**: Larger models with quantization

## 🚨 Troubleshooting

### Ollama Issues

**Service not starting:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Test with a simple prompt
ollama run llama3.1:8b "Hello, how are you?"
```

**Model not found:**
```bash
# List available models
ollama list

# Pull the model you want
ollama pull llama3.1:8b
```

### Llama.cpp Issues

**Model loading fails:**
- Check file path in `.env`
- Verify model is a valid GGUF format
- Ensure sufficient RAM/VRAM

**Slow performance:**
- Increase `LLAMACPP_N_THREADS` (don't exceed CPU cores)
- Enable GPU acceleration with `LOCAL_GPU_LAYERS`
- Use a smaller or more quantized model

### Memory Issues

**Out of memory errors:**
- Use smaller models (3B instead of 7B parameters)
- Reduce `LLAMACPP_N_CTX` context size
- Close other applications

## ✅ Testing Your Setup

### 1. Configuration Check
```bash
python main.py --config-check
```

### 2. Basic AI Test
```bash
python test_config.py
```

### 3. Full Analysis Test
```bash
python main.py --mode quick --ai-analysis
```

## 🔐 Privacy Benefits

Local LLMs provide several advantages:

- **Complete Privacy**: Your LinkedIn data never leaves your machine
- **No API Costs**: No charges for AI analysis
- **Offline Capability**: Works without internet connection
- **Data Control**: Full control over your analysis process
- **Customization**: Can fine-tune models for your specific needs

## 🎯 Example Usage Scenarios

### Daily LinkedIn Analysis
```bash
# Quick morning check with local AI
python main.py --mode quick --ai-analysis --notifications
```

### Weekly Deep Dive
```bash
# Comprehensive analysis with all features
python main.py --mode intelligence --all-data --ai-analysis
```

### Company Research
```bash
# Target specific company analysis
python main.py --company "Microsoft" --ai-analysis --format json
```

## 📈 Performance Optimization

### For CPU-only Systems:
```env
LLAMACPP_N_THREADS=8  # Match your CPU cores
LOCAL_GPU_LAYERS=0
LLAMACPP_N_CTX=2048   # Smaller context for speed
```

### For GPU Systems:
```env
LOCAL_GPU_LAYERS=20   # Offload layers to GPU
LLAMACPP_N_CTX=4096   # Larger context possible
```

## 🔄 Switching Between Models

You can easily switch between local and cloud models by changing your `.env`:

```env
# Use Ollama
AI_PROVIDER=ollama

# Use Claude (requires API key)
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your-key

# Use OpenAI (requires API key)  
AI_PROVIDER=openai
OPENAI_API_KEY=your-key
```

Your Job Search Intelligence will automatically use the configured provider! 🎉
