# CAD Validator — Setup & Run Guide (Windows)

## One-Time Setup

1. Install Python 3.10+ from python.org (check "Add to PATH" during install)

2. Open Command Prompt in the project folder:

```
cd path\to\cad-validator
pip install -r requirements.txt
```

3. Set your API key (get free key from console.anthropic.com):

```
set ANTHROPIC_API_KEY=your_key_here
```

## Run the App

```
python app.py
```

Open your browser and go to: http://localhost:5000

## Test with a Sample STL File

Download any STL from:
- https://grabcad.com (search "bracket" or "housing")
- https://www.thingiverse.com

Upload it in the web app and click "Validate with AI"

## Project Structure

```
cad-validator/
├── app.py                          ← Flask server (entry point)
├── requirements.txt                ← Python dependencies
├── uploads/                        ← Uploaded files stored here (auto-created)
├── backend/
│   └── modules/
│       ├── geometry_extractor.py   ← Reads STL geometry
│       ├── rule_checker.py         ← Deterministic rule checks
│       ├── ai_validator.py         ← Claude AI validation
│       └── report_generator.py    ← PDF report generation
└── frontend/
    └── templates/
        └── index.html              ← Full web UI with 3D viewer
```

## Team Division

| Member | Files to work on |
|--------|-----------------|
| Member 1 | geometry_extractor.py, rule_checker.py |
| Member 2 | ai_validator.py (AI prompts, chat) |
| Member 3 | index.html (UI improvements, styling) |

## Common Issues

- **"Module not found"**: Run `pip install -r requirements.txt` again
- **API key error**: Make sure `set ANTHROPIC_API_KEY=...` was run in same CMD window
- **STL not loading**: Use binary STL format (most CAD tools export binary by default)
- **Port in use**: Change `port=5000` to `port=5001` in app.py
