# 📦 Dependencies & Requirements - Job Search Intelligence

## 🔧 Updated Dependencies for Modular Architecture

The Job Search Intelligence has been updated with all necessary dependencies for the new modular architecture. All packages have been validated and are compatible with the organized codebase.

## 📋 Core Dependencies Overview

### **🌐 Web Automation & LinkedIn Integration**
```
selenium==4.x.x               # Web automation framework
webdriver-manager==4.0.2      # Automatic WebDriver management
linkedin-api==2.3.1           # LinkedIn API integration
beautifulsoup4==4.13.4        # HTML parsing and scraping
lxml==5.4.0                   # XML/HTML processing
requests==2.32.4              # HTTP library
aiohttp==3.12.15              # Async HTTP client/server
```

### **📊 Data Analysis & Visualization**
```
pandas==2.3.1                 # Data manipulation and analysis
numpy==1.26.4                 # Numerical computing
plotly==6.3.1                 # Interactive visualizations
matplotlib==3.10.6            # Statistical plotting (installed during setup)
seaborn==0.13.2               # Statistical data visualization (installed during setup)
```

### **🤖 AI & Machine Learning**
```
openai==1.100.0               # OpenAI API integration
anthropic==0.60.0             # Claude API integration
ollama==0.5.1                 # Local LLM integration
tqdm==4.67.1                  # Progress bars for AI operations
```

### **🗄️ Database & Storage**
```
aiosqlite==0.21.0             # Async SQLite database (installed during setup)
SQLAlchemy==2.0.43            # SQL toolkit and ORM
psycopg==3.2.9                # PostgreSQL adapter
openpyxl==3.1.5               # Excel file handling
xlsxwriter==3.2.9             # Excel file creation
```

### **🔧 System & Monitoring**
```
psutil==5.9.8                 # System and process monitoring (installed during setup)
aiofiles==0.8.0               # Async file operations
configparser==5.3.0           # Configuration file parsing
python-dotenv==0.21.1         # Environment variable management
```

### **📱 Notifications & Integrations**
```
Telethon==1.40.0              # Telegram API integration
twilio==8.13.0                # SMS/Voice notifications
```

## 🛠️ Development & Testing Dependencies

### **🧪 Testing Framework**
```
pytest==7.4.4                 # Testing framework
pytest-asyncio==0.23.8        # Async testing support
pytest-cov==4.1.0             # Coverage reporting
pytest-mock==3.14.1           # Mocking for tests
pytest-html==4.1.1            # HTML test reports
coverage==7.10.1              # Code coverage analysis
```

### **🔍 Code Quality**
```
black==23.12.1                # Code formatting
flake8==6.1.0                 # Code linting
isort==5.13.2                 # Import sorting
mypy==1.17.0                  # Static type checking
```

### **📈 Performance & Profiling**
```
memory-profiler==0.61.0       # Memory usage profiling
line_profiler==5.0.0          # Line-by-line profiling
py-cpuinfo==9.0.0            # CPU information
```

## 🎯 Module-Specific Dependencies

### **Core Module (`src/core/`)**
```
selenium                      # Web automation for LinkedIn
webdriver-manager            # WebDriver management
linkedin-api                 # LinkedIn API wrapper
aiosqlite                    # Async database operations
psutil                       # System monitoring
```

### **Analytics Module (`src/analytics/`)**
```
pandas                       # Data analysis
numpy                        # Numerical computations
matplotlib                   # Statistical plotting
seaborn                      # Advanced visualizations
plotly                       # Interactive charts
```

### **Intelligence Module (`src/intelligence/`)**
```
openai                       # OpenAI GPT integration
anthropic                    # Claude AI integration
ollama                       # Local LLM support
tqdm                         # Progress tracking
```

### **Tracking Module (`src/tracking/`)**
```
plotly                       # Dashboard visualizations
openpyxl                     # Excel report generation
xlsxwriter                   # Advanced Excel features
pandas                       # Data processing
```

## 🚀 Installation Commands

### **Complete Installation**
```bash
# Install all dependencies from updated requirements.txt
pip install -r requirements.txt
```

### **Module-Specific Installation**
```bash
# Core functionality only
pip install selenium webdriver-manager linkedin-api aiosqlite psutil

# Analytics capabilities
pip install pandas numpy matplotlib seaborn plotly

# AI features
pip install openai anthropic ollama tqdm

# Tracking and reporting
pip install plotly openpyxl xlsxwriter
```

### **Development Environment**
```bash
# Development and testing tools
pip install pytest pytest-asyncio pytest-cov black flake8 isort mypy
```

## 🔄 Dependency Installation During Repository Organization

During the repository organization process, the following dependencies were automatically installed:

✅ **matplotlib==3.10.6** - For analytics module visualization  
✅ **seaborn==0.13.2** - For statistical plotting in analytics  
✅ **psutil==7.1.0** - For system monitoring capabilities  
✅ **aiosqlite==0.21.0** - For async database operations  

All dependencies are now properly installed and validated for the modular architecture.

## 🐍 Python Version Compatibility

**Minimum Python Version:** 3.8+  
**Recommended Python Version:** 3.9+  
**Tested Python Versions:** 3.8, 3.9, 3.10, 3.11, 3.12

### **Version-Specific Notes**
- **Python 3.8+**: Required for async/await syntax
- **Python 3.9+**: Recommended for optimal performance
- **Python 3.10+**: Enhanced type hints support
- **Python 3.11+**: Improved async performance

## 🔒 Security Dependencies

### **Cryptography & Security**
```
cryptography==41.0.7          # Encryption and security
PyJWT==2.10.1                 # JSON Web Token handling
PySocks==1.7.1                # SOCKS proxy support
```

### **HTTP Security**
```
certifi==2025.7.14            # SSL certificate verification
urllib3==2.5.0                # HTTP library with security features
```

## 📊 Dependency Categories Summary

| Category | Package Count | Key Packages |
|----------|---------------|--------------|
| **Core Functionality** | 15 | selenium, pandas, aiohttp |
| **AI/ML Integration** | 8 | openai, anthropic, ollama |
| **Data Visualization** | 6 | plotly, matplotlib, seaborn |
| **Database & Storage** | 5 | aiosqlite, SQLAlchemy, openpyxl |
| **Testing & Quality** | 12 | pytest, black, mypy |
| **System & Monitoring** | 4 | psutil, aiofiles |
| **Notifications** | 3 | Telethon, twilio |
| **Development Tools** | 8 | black, flake8, isort |

**Total Dependencies:** ~60 packages  
**Core Runtime Dependencies:** ~35 packages  
**Development Dependencies:** ~25 packages  

## 🚨 Important Notes

### **LinkedIn API Compliance**
- `linkedin-api==2.3.1` - Unofficial LinkedIn API wrapper
- `selenium` + `webdriver-manager` - For web automation compliance
- Rate limiting packages ensure LinkedIn ToS compliance

### **AI Provider Requirements**
- **OpenAI**: Requires API key for GPT models
- **Anthropic**: Requires API key for Claude models  
- **Ollama**: Local installation required for offline AI

### **Database Requirements**
- **SQLite**: Built-in Python support via aiosqlite
- **PostgreSQL**: Optional, requires psycopg package
- **Excel Files**: Supported via openpyxl and xlsxwriter

## 🔄 Maintenance & Updates

### **Regular Updates**
```bash
# Check for outdated packages
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade package_name
```

### **Security Updates**
```bash
# Check for security vulnerabilities
pip-audit

# Update security-critical packages
pip install --upgrade cryptography certifi urllib3
```

## 📝 Requirements.txt Structure

The `requirements.txt` file contains all dependencies with pinned versions for reproducible installations. The file is automatically generated from the virtual environment and includes:

1. **Pinned Versions**: Exact version numbers for stability
2. **Complete Dependency Tree**: All sub-dependencies included
3. **Tested Combinations**: All packages verified to work together
4. **Security Patches**: Latest security updates included

---

**💡 Tip**: Use `pip freeze > requirements.txt` to update the requirements file after installing new packages.