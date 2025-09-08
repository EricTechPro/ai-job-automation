# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Browser Automation** system for job applications using **Claude Computer Use** via Hyperbrowser. The system intelligently searches for Developer Advocate positions, analyzes job listings, and can automatically fill out job applications using Claude's computer interaction capabilities.

**Key Enhancement**: Uses Claude Computer Use for direct browser interaction, enabling form filling, clicking, and complete job application workflows with persistent job tracking.

## Development Setup

### Environment Setup
```bash
# Activate virtual environment 
source venv/bin/activate

# Install dependencies (includes anthropic for Computer Use)
pip install -r requirements.txt
```

### Required Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Required keys:
- `HYPERBROWSER_API_KEY`: For cloud browser automation
- `ANTHROPIC_API_KEY`: Optional, for custom Claude Computer Use quota

### Running the Application
```bash
# Test the system first
python3 tests/test_system.py

# Run the full job automation
python3 main.py
```

## Architecture

### Core Components

**DeveloperAdvocateJobBot** (`main.py:29`)
- Main orchestrator with Claude Computer Use integration
- Integrates resume, preferences, and personal info into AI context
- Manages job search and application workflows with persistent tracking

**BrowserAgent** (`browser_agent.py:16`)
- `execute_computer_use_task()` - Direct Claude Computer Use integration
- `search_and_analyze_jobs()` - Intelligent job search with Computer Use
- `apply_to_job()` - Automated job application filling
- `analyze_job_page()` - Extract detailed job information
- `check_application_status()` - Check application status through portals

**JobTracker** (`utils/job_tracker.py:29`)
- Persistent JSON-based job database
- Status tracking: FOUND → REVIEWED → APPLIED → INTERVIEW → OFFER
- Export capabilities and comprehensive statistics
- Automatic backups and duplicate detection

**Logger** (`utils/logger.py:44`)
- Color-coded logging system
- Specialized job-related logging methods
- File and console output with appropriate formatting

### Key Dependencies
- **hyperbrowser**: Cloud browser with Claude Computer Use support
- **anthropic**: Direct Anthropic API access (optional)
- **PyPDF2**: Resume PDF text extraction
- **python-dotenv**: Environment variable management
- **colorama**: Cross-platform colored terminal output

### Computer Use Workflow
1. Load resume PDF + JSON preferences from `user/` folder → AI context
2. **Claude Computer Use** searches job boards directly (LinkedIn, Indeed, etc.)
3. AI intelligently navigates pages, clicks, and extracts job information
4. Jobs are automatically tracked in `data/job_tracker_data.json`
5. **Claude Computer Use** fills out job applications automatically
6. All activities logged with colored output and exported to CSV

### Enhanced Functions

**Job Search** (`search_and_analyze_jobs()`):
- Navigates to major job boards
- Searches for specific role types
- Analyzes 10-15 listings per search
- Extracts matching jobs with AI reasoning
- Automatically saves to job tracker

**Job Application** (`apply_to_job()`):
- Fills out application forms automatically
- Handles personal information fields
- Provides thoughtful responses to application questions
- Updates job status in tracker
- Takes confirmation screenshots

**Job Tracking** (`JobTracker` class):
- Persistent storage in JSON format
- Comprehensive status management
- Search and filtering capabilities
- CSV export for data analysis
- Statistics and reporting

### User Configuration Files
- `user/job_preferences.json`: Target roles, companies, salary range, tech stack
- `user/personal_info.json`: Contact details, current role, work authorization  
- `user/Eric_Wu_Resume.pdf`: Resume file for text extraction (user should replace)
- `.env`: API keys for Hyperbrowser and Anthropic

### Data Files (Auto-created)
- `data/job_tracker_data.json`: Persistent job application database
- `data/job_tracker_export.csv`: Exportable spreadsheet format
- `job_bot.log`: Application logs with colored terminal output

## Testing

Test the complete system:
```bash
python tests/test_system.py
```

Test individual components:
```bash
# Basic browser connection test
python3 tests/test_computer_use.py

# Test Computer Use functionality  
python -c "from browser_agent import BrowserAgent; print('Computer Use integration loaded')"
```

## Project Structure
```
ai-browser-automation/
├── main.py                    # Main application with Computer Use integration
├── browser_agent.py           # Claude Computer Use automation agent
├── utils/                     # Utility modules
│   ├── __init__.py            # Package exports
│   ├── logger.py              # Colored logging system
│   └── job_tracker.py         # Job tracking and status management
├── user/                      # User configuration (replace with your data)
│   ├── job_preferences.json   # Job search criteria
│   ├── personal_info.json     # Personal/contact information
│   └── Eric_Wu_Resume.pdf     # Resume PDF file
├── data/                      # Application data (auto-created)
│   ├── job_tracker_data.json  # Job database
│   └── job_tracker_export.csv # CSV export
├── tests/                     # Test suite
│   ├── test_system.py         # Comprehensive system tests
│   └── test_computer_use.py   # Basic integration tests
├── docs/                      # Documentation
│   ├── CLAUDE.md              # This file
│   ├── REFACTORING_GUIDE.md   # Detailed technical documentation
│   └── PROJECT_STRUCTURE.md   # Project organization overview
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
└── venv/                     # Python virtual environment
```

## Current Capabilities

✅ **Implemented**:
- Claude Computer Use integration with Hyperbrowser
- Intelligent job search across multiple platforms
- Automated job application form filling
- Resume and preference loading from user folder
- Persistent job tracking with status management
- Comprehensive error handling and session management
- Color-coded logging system
- CSV export for data analysis

✅ **New Features**:
- Direct browser interaction (no screenshot analysis)
- Form filling and clicking automation  
- Multi-step job application workflows
- Session reuse for efficiency
- Detailed action summaries and confirmations
- Job status tracking through entire application process
- Statistics and reporting capabilities

## Usage Examples

**Setup your profile first:**
1. Replace files in `user/` folder with your information
2. Update `user/job_preferences.json` with your criteria
3. Update `user/personal_info.json` with your contact details
4. Add your resume PDF to `user/` folder

**Search for jobs:**
```python
# Will intelligently search and analyze jobs, automatically tracking them
python3 main.py
```

**Apply to specific job:**
```python
# Use the apply_to_job method with tracked job IDs
# Jobs are automatically tracked in data/job_tracker_data.json
```

**View your applications:**
```bash
# Check JSON database
cat data/job_tracker_data.json

# View CSV export
open data/job_tracker_export.csv
```

## Open Source Considerations

This project is designed to be easily reusable:

1. **User Data Separation**: All user-specific data is in the `user/` folder
2. **Persistent Tracking**: Job applications are tracked across sessions
3. **Export Capabilities**: Data can be exported for analysis
4. **Comprehensive Logging**: All activities are logged for debugging
5. **Modular Architecture**: Components can be used independently

To make it your own:
1. Replace files in `user/` folder with your information
2. Set up your API keys in `.env`
3. Run the system and track your job applications

## Key Improvements for Open Source

- **🗂️ Clean Structure**: Separated user data, code, and documentation
- **💾 Persistent Tracking**: Never lose job application data
- **🎨 Visual Feedback**: Color-coded logs for clear status updates  
- **📊 Analytics**: Export job data for analysis and reporting
- **🧪 Testing**: Comprehensive test suite for reliability
- **📚 Documentation**: Clear setup and usage instructions