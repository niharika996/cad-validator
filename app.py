from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()

# IMPORTANT: Tell Flask where to find templates (in frontend/templates)
template_dir = os.path.abspath('frontend/templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Import all modules ──
from backend.modules.geometry_extractor import extract_geometry
from backend.modules.rule_checker import run_rule_checks
from backend.modules.ai_validator import run_ai_validation
from backend.modules.report_generator import generate_pdf_report

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Save uploaded file
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        # Step 1: Extract geometry
        geometry = extract_geometry(filepath)

        # Step 2: Rule-based checks
        rule_violations = run_rule_checks(geometry)

        # Step 3: AI validation
        ai_result = run_ai_validation(geometry, rule_violations)

        # Step 4: Build final result
        result = {
            'geometry': geometry,
            'rule_violations': rule_violations,
            'ai_analysis': ai_result,
            'compliance_score': calculate_score(rule_violations, ai_result),
            'filename': file.filename
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()
    pdf_path = generate_pdf_report(data)
    return send_file(pdf_path, as_attachment=True, download_name='validation_report.pdf')

@app.route('/chat', methods=['POST'])
def chat():
    from backend.modules.ai_validator import answer_question
    data = request.get_json()
    question = data.get('question', '')
    context = data.get('context', {})
    
    # Make sure rule_violations are passed
    if 'rule_violations' not in context and 'rule_violations' in data:
        context['rule_violations'] = data['rule_violations']
    
    answer = answer_question(question, context)
    return jsonify({'answer': answer})

def calculate_score(rule_violations, ai_result):
    score = 100
    for v in rule_violations:
        if v['severity'] == 'CRITICAL':
            score -= 15
        elif v['severity'] == 'WARNING':
            score -= 7
        elif v['severity'] == 'INFO':
            score -= 2
    score -= ai_result.get('score_deduction', 0)
    return max(0, score)

if __name__ == '__main__':
    app.run(debug=True, port=5000)