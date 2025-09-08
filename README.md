# AI Job Automation System

Automated job search and application system using Claude Computer Use to intelligently find and apply to jobs based on your preferences. Configurable for any job type through user preferences.

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

1. **Add your resume**: Place your resume PDF in `user/` folder (replace existing file)
2. **Edit job preferences** (`user/job_preferences.json`):
   ```json
   {
     "target_roles": ["Developer Advocate", "Software Engineer", "DevRel"],
     "preferred_companies": ["OpenAI", "Google", "Meta"],
     "min_salary": 150000,
     "remote_preference": "remote_or_hybrid"
   }
   ```
3. **Edit personal info** (`user/personal_info.json`):
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
│   └── Eric_Wu_Resume.pdf     # Your resume (replace this file)
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