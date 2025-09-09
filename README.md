# AI Job Automation System

Automated job search and application system using Claude Computer Use to intelligently find and apply to jobs based on your preferences. Configurable for any job type through user preferences.

## 🏗️ System Architecture

```mermaid
graph TD
    %% User Input Layer
    A[👤 User Input<br/>• Resume PDF<br/>• Job Preferences<br/>• Personal Info] 
    B[🧠 AI Context<br/>• Resume Text<br/>• Personal Info<br/>• Target Roles]
    C[⚙️ Configuration<br/>• Job Preferences<br/>• Platform Config<br/>• Anti-Detection]
    
    %% Main System
    D[🤖 Main System<br/>(main.py)<br/>• Initialization<br/>• AI Context<br/>• Job Tracking]
    
    %% Core Components
    E[🔄 Multi-Browser Manager<br/>• Orchestration<br/>• Concurrency<br/>• Session Mgmt]
    F[🥷 Anti-Detection Config<br/>• Stealth Mode<br/>• Device Rotation<br/>• Delay Control]
    G[📊 Job Tracker<br/>• Data Storage<br/>• Status Updates<br/>• JSON Export]
    
    %% Browser Sessions
    H[🌐 Concurrent Browser Sessions]
    
    %% Job Platforms  
    I1[🔍 RemoteOK<br/>Public • No Auth]
    I2[🔍 WeWorkRemotely<br/>Public • No Auth] 
    I3[🔍 AngelList<br/>Public • No Auth]
    I4[🔍 Dice<br/>Public • No Auth]
    I5[🔍 + 8 More Sites<br/>Public • No Auth]
    
    %% Browser Agent
    J[🤖 Browser Agent<br/>(browser_agent.py)<br/>• Claude Computer Use<br/>• Job Search<br/>• Form Automation<br/>• Result Processing]
    
    %% Hyperbrowser API
    K[🌐 Hyperbrowser API<br/>• Browser Session Mgmt<br/>• Claude Computer Use<br/>• Anti-Detection<br/>• Live URLs & Recordings]
    
    %% Results Processing
    L[📈 Results Processing<br/>• Real Job URL Extraction<br/>• Structured Data Parsing<br/>• Company & Salary Info<br/>• Application Status]
    
    %% Output Data
    M[💾 Output Data<br/>• jobs.json<br/>• CSV Export<br/>• Colored Logs<br/>• Live Browser URLs]
    
    %% Connections
    A --> B
    C --> B
    B --> D
    D --> E
    D --> F  
    D --> G
    E -.-> F
    E --> H
    H --> I1
    H --> I2
    H --> I3
    H --> I4
    H --> I5
    I1 --> J
    I2 --> J
    I3 --> J
    I4 --> J
    I5 --> J
    J <--> K
    J --> L
    L --> G
    L --> M
    G --> M
    
    %% Styling
    classDef userInput fill:#e1f5fe
    classDef mainSystem fill:#f3e5f5  
    classDef processing fill:#fff3e0
    classDef platforms fill:#e8f5e8
    classDef output fill:#fce4ec
    
    class A,B,C userInput
    class D mainSystem
    class E,F,G,J,K,L processing
    class H,I1,I2,I3,I4,I5 platforms
    class M output
```

### 🔄 Workflow Process

1. **Initialization**: Load resume PDF, job preferences, and platform configurations
2. **AI Context Creation**: Build comprehensive context for Claude Computer Use
3. **Multi-Browser Launch**: Simultaneously start sessions across 12+ job platforms  
4. **Intelligent Search**: Claude Computer Use navigates and searches each platform
5. **Job Processing**: Extract, analyze, and store job listings with status tracking
6. **Data Persistence**: Save all results to `data/jobs.json` with structured data
7. **Live Monitoring**: View real-time browser sessions and execution recordings

### 📊 Sample Output Data

The system generates structured job data in `data/jobs.json`:

```json
[
  {
    "company": "InnovateLabs",
    "job_title": "Developer Relations Engineer", 
    "location": "San Francisco, CA",
    "job_url": "https://remoteok.com/jobs/innovatelabs-developer-relations-engineer",
    "salary_range": "$140k-190k",
    "status": "found",
    "last_updated": "2025-09-08T18:41:53.041407",
    "job_board": ""
  },
  {
    "company": "TechCorp",
    "job_title": "Developer Experience Engineer",
    "location": "Remote", 
    "job_url": "https://weworkremotely.com/jobs/techcorp-developer-experience-engineer",
    "salary_range": "$140k-190k",
    "status": "found",
    "last_updated": "2025-09-08T18:50:58.051007",
    "job_board": ""
  }
]
```

**Job Status Tracking**:
- `found` - Job discovered and saved
- `applied` - Application submitted
- `rejected` - Application rejected
- `interview` - Interview scheduled

## Features

- 🔍 **Intelligent Job Search** - Automatically searches multiple job boards
- 🤖 **Claude Computer Use** - AI-powered browser automation for form filling
- 📊 **Job Tracking** - Tracks all applications with status updates
- 🎨 **Colored Logging** - Clear visibility with color-coded log messages
- 📁 **Data Persistence** - Never lose track of your applications

## Quick Start

### 1. Prerequisites

- Python 3.8+
- [Hyperbrowser API Key](https://www.hyperbrowser.ai/)
- Resume PDF file

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-browser-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key:
HYPERBROWSER_API_KEY=your_key_here
```

### 4. Setup Your Profile

**REQUIRED**: You must configure these files before running the application:

1. **Add your resume**: Place your resume PDF as `user/Resume.pdf` (exactly this filename)
2. **Copy and edit personal info**:
   ```bash
   cp user/personal_info.example.json user/personal_info.json
   # Edit user/personal_info.json with your actual information
   ```
3. **Copy and edit job preferences**:
   ```bash
   cp user/job_preferences.example.json user/job_preferences.json
   # Edit user/job_preferences.json with your job criteria
   ```

Example job preferences (`user/job_preferences.json`):
   ```json
   {
     "target_roles": ["Developer Advocate", "Software Engineer", "DevRel"],
     "preferred_companies": ["OpenAI", "Google", "Meta"],
     "min_salary": 150000,
     "remote_preference": "remote_or_hybrid"
   }
   ```

Example personal info (`user/personal_info.json`):
   ```json
   {
     "first_name": "Your",
     "last_name": "Name",
     "email": "your.email@example.com",
     "phone": "+1234567890",
     "linkedin": "https://linkedin.com/in/yourprofile"
   }
   ```

### 5. Run the Application

```bash
# Test the setup
python3 tests/test_system.py

# Start job search and application
python3 main.py
```

## How It Works

1. **Loads your profile** - Extracts text from resume PDF and loads preferences
2. **Searches job boards** - Uses Claude to navigate LinkedIn, Indeed, etc.
3. **Analyzes matches** - AI evaluates jobs against your profile
4. **Tracks applications** - Saves all jobs to `data/job_tracker_data.json`
5. **Applies automatically** - Can fill out application forms (optional)

## File Structure

```
├── main.py                    # Main application
├── browser_agent.py           # Browser automation
├── utils/                     # Logging & job tracking
├── user/                      # Your configuration (replace with your data)
│   ├── job_preferences.json   # Your job criteria
│   ├── personal_info.json     # Your contact info
│   └── Resume.pdf             # Your resume (replace this file)
├── data/                      # Application tracking data (auto-created)
│   ├── job_tracker_data.json  # Job database
│   └── job_tracker_export.csv # Export file
├── tests/                     # Test files
├── docs/                      # Documentation
└── venv/                      # Python virtual environment
```

## Viewing Your Applications

```bash
# Check the JSON file for detailed tracking
cat data/job_tracker_data.json

# Or export to spreadsheet
# This creates data/job_tracker_export.csv
```

## Tips

- 🎯 Start with specific job titles for better results
- 📝 Review `data/job_tracker_data.json` to see all found jobs
- ⏰ Add delays between applications to be respectful
- 🔍 Check `job_bot.log` for detailed execution logs

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No API key | Sign up at [hyperbrowser.ai](https://www.hyperbrowser.ai/) |
| Resume not found | Ensure PDF is in `user/` folder |
| No jobs found | Try different search terms in the code |
| Colors not working | Run `pip install colorama` |

## Support

- Check `docs/REFACTORING_GUIDE.md` for detailed documentation
- Review `job_bot.log` for debugging information
- Test individual components with `tests/test_system.py`

---

**Note**: This tool is for educational purposes. Always review applications before submission and respect website terms of service.