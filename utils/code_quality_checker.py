import os
import re
import time
import json
import subprocess
import difflib
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import autoflake
import black
import isort
import ast
import tracemalloc
import threading
from datetime import datetime, timedelta
# import logging

# # Disable Flask's access logs, but keep startup messages
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)  # Suppress access logs (requests)

# # You can re-enable the logging for server startup with a different log level
# logging.basicConfig(level=logging.INFO)  # This allows startup logs to be shown


app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'py', 'js'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# AST-Based Optimizations (For Python)
class ASTOptimizer(ast.NodeTransformer):
    def visit_If(self, node):
        if isinstance(node.test, ast.Constant) and node.test.value is False:
            return None
        return self.generic_visit(node)

    def visit_Compare(self, node):
        if (isinstance(node.left, ast.Name) and
            isinstance(node.comparators[0], ast.Constant)):
            val = node.comparators[0].value
            if val is True:
                return node.left
            elif val is False:
                return ast.UnaryOp(op=ast.Not(), operand=node.left)
        return node

    def visit_Assign(self, node):
        return node

def ast_optimize_code(code: str) -> str:
    try:
        tree = ast.parse(code)
        transformer = ASTOptimizer()
        optimized_tree = transformer.visit(tree)
        ast.fix_missing_locations(optimized_tree)
        return ast.unparse(optimized_tree)
    except Exception as e:
        return code

# Core Code Quality Checker
class CodeQualityChecker:
    def __init__(self, file_path, language):
        self.file_path = file_path
        self.language = language
        self.optimized_code = None
        self.original_code = self._read_code()

    def _read_code(self):
        with open(self.file_path, "r") as f:
            return f.read()

    def _write_code(self, code):
        with open(self.file_path, "w") as f:
            f.write(code)

    def run_subprocess_json(self, command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if result.returncode != 0 and result.stderr:
        # Log errors to a file or suppress it
            print(f"Error in subprocess: {result.stderr}")
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return {}

    def run_pylint(self):
        return self.run_subprocess_json(["pylint", self.file_path, "--output-format=json"])

    def run_bandit(self):
        return self.run_subprocess_json(["bandit", "-r", self.file_path, "-f", "json"])

    def check_cyclomatic_complexity(self):
        return self.run_subprocess_json(["radon", "cc", self.file_path, "--json"])
    
    def format_cyclomatic_complexity(cyclomatic_data):
        """Formats the cyclomatic complexity data into a more detailed and user-friendly string."""

        formatted_output = ""
        for file, functions in cyclomatic_data.items():
            formatted_output += f"File: {file}\n"
            for function in functions:
                function_name = function.get('name', 'Unknown Function')
                complexity_score = function.get('complexity', 'N/A')
                rank = function.get('rank', 'N/A')
                start_line = function.get('lineno', 'N/A')
                end_line = function.get('endline', 'N/A')
                closures = function.get('closures', [])
                
                # Generate the closures text (if any)
                closure_text = "None" if not closures else ", ".join(closures)
                
                # Create the detailed report for each function
                formatted_output += (
                    f"  Function: {function_name}\n"
                    f"    - Cyclomatic Complexity: {complexity_score}\n"
                    f"    - Rank: {rank}\n"
                    f"    - Location: Lines {start_line} to {end_line}\n"
                    f"    - Closures: {closure_text}\n"
                )
            formatted_output += "\n"

        return formatted_output

    def remove_unused_imports(self):
        subprocess.run(["autoflake", "--in-place", "--remove-unused-variables", "--remove-all-unused-imports", self.file_path])

    def format_code(self):
        if self.language == "python":
            code = self._read_code()
            formatted = black.format_str(code, mode=black.FileMode())
            self._write_code(formatted)

    def sort_imports(self):
        if self.language == "python":
            subprocess.run(["isort", self.file_path])

    def ast_cleanup(self):
        if self.language == "python":
            code = self._read_code()
            optimized = ast_optimize_code(code)
            self._write_code(optimized)

    def optimize_code(self):
        if self.language == "python":
            self.remove_unused_imports()
            self.format_code()
            self.sort_imports()
            self.ast_cleanup()

        final_code = self._read_code()
        self.optimized_code = final_code
        return final_code

    def get_diff(self):
        optimized_lines = self.optimized_code.splitlines()
        original_lines = self.original_code.splitlines()
        diff = difflib.unified_diff(original_lines, optimized_lines, lineterm='')
        return '\n'.join(diff)

    def check_code_quality(self):
        return {
            "optimized_code": self.optimized_code,
            "diff": self.get_diff()
        }

# JavaScript-specific optimizations
class JavaScriptCodeOptimizer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.original_code = self._read_code()
        self.optimized_code = self.optimize_code()

    def _read_code(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def optimize_code(self):
        code = self.original_code
        code = re.sub(r"(?:let|const|var)\s+\w+\s*=\s*[^;\n]+;\s*//\s*This variable is never used", "", code)
        code = re.sub(r"if\s*\(\s*false\s*\)\s*\{(?:[^{}]*|\{[^{}]*\})*\}", "", code, flags=re.MULTILINE)
        code = re.sub(r"if\s*\(\s*(\w+)\s*===\s*true\s*\)", r"if (\1)", code)
        code = re.sub(r"if\s*\(\s*(\w+)\s*===\s*false\s*\)", r"if (!\1)", code)
        code = re.sub(r"\bvar\b", "let", code)
        code = re.sub(r'"([^"]*?)"\s*\+\s*(\w+)', r'\1${\2}', code)
        code = re.sub(r"(\w+)\s*\+\s*\"([^\"]*?)\"", r'${\1}\2', code)
        code = re.sub(r'\n\s*\n+', '\n\n', code).strip()
        return code

    def _run_json(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            return json.loads(result.stdout or "[]")
        except Exception as e:
            print(f"Error: {e}")
            return []

    def run_eslint(self):
        try:
            command = ["eslint", self.file_path, "--format", "json"]
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            return json.loads(result.stdout or "[]")
        except Exception as e:
            print(f"ESLint run error: {e}")
            return []


    def check_code_quality(self):
        return {
            "optimized_code": self.optimized_code,
            "diff": '\n'.join(difflib.unified_diff(
                self.original_code.splitlines(),
                self.optimized_code.splitlines()
            )),
            "eslint_results": self.run_eslint(),
        }

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/check_code_quality", methods=["POST"])
def check_code_quality():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid or empty file"}), 400

        ext = file.filename.rsplit('.', 1)[1].lower()
        language = {"py": "python", "js": "javascript"}.get(ext)
        timestamp = int(time.time())
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        tracemalloc.start()
        start_time = time.time()


        if language == "python":
            checker = CodeQualityChecker(file_path, language)
        elif language == "javascript":
            checker = JavaScriptCodeOptimizer(file_path)
        else:
            return jsonify({"status": "error", "message": "Unsupported language"}), 400

        checker.optimize_code()
        result = checker.check_code_quality()
        
        execution_time = round(time.time() - start_time, 3)
        current, peak = tracemalloc.get_traced_memory()
        memory_usage_kb = round(peak / 1024, 2)
        tracemalloc.stop()

        optimized_filename = f"optimized_{filename}"
        optimized_file_path = os.path.join(app.config['UPLOAD_FOLDER'], optimized_filename)
        with open(optimized_file_path, "w") as f:
            f.write(result["optimized_code"])

        return jsonify({
            "status": "success",
            "message": "Code optimized and checked",
            "optimized_code": result["optimized_code"],
            "diff": result["diff"],
            "eslint_results": result.get("eslint_results"),
            "execution_time": execution_time,
            "memory_usage_kb": memory_usage_kb,
            "download_url": f"/uploads/{optimized_filename}"
        })

    except Exception as e:
        app.logger.error(f"Exception occurred: {str(e)}")
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@app.route("/analyze_code_quality", methods=["POST"])
def analyze_code_quality():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        file = request.files.get('file')
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid or empty file"}), 400

        ext = file.filename.rsplit('.', 1)[1].lower()
        language = {"py": "python", "js": "javascript"}.get(ext)
        timestamp = int(time.time())
        filename = f"analysis_{timestamp}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        tracemalloc.start()
        start_time = time.time()

        if language == "javascript":
            checker = JavaScriptCodeOptimizer(file_path)
            eslint_results = checker.run_eslint()

            if not eslint_results:
                return jsonify({
                    "status": "error",
                    "message": "ESLint did not return any results. Please ensure ESLint is installed."
                }), 400

            first_result = eslint_results[0]
            messages = first_result.get("messages", [])

            def format_msg(msg):
                rule_id = msg.get("ruleId", "unknown")
                line = msg.get("line", "?")
                column = msg.get("column", "?")
                return f"'{msg.get('message')}' (line {line}, column {column}, rule: {rule_id})"

            def unique_messages(msg_list):
                seen = set()
                unique = []
                for msg in msg_list:
                    formatted = format_msg(msg)
                    if formatted not in seen:
                        seen.add(formatted)
                        unique.append(formatted)
                return unique

            analysis = {
                "bug_count": len(messages),
                "code_smells": unique_messages([msg for msg in messages if msg.get("severity") == 1]),
                "coding_standard_violations": unique_messages([msg for msg in messages if msg.get("severity") == 2]),
                "deprecated_rules": first_result.get("usedDeprecatedRules", []),
                "unused_variables": unique_messages([msg for msg in messages if "unused" in msg.get("message", "").lower()]),
                "security_issues": [format_msg(msg) for msg in messages if "security" in msg.get("ruleId", "").lower()],
                "indentation_issues": unique_messages([msg for msg in messages if "indentation" in msg.get("message", "").lower()]),
                "unused_imports": unique_messages([msg for msg in messages if "unused-import" in msg.get("ruleId", "").lower()])
            }

            # Formatting the response properly to include more detailed information
            analysis_summary = {
                "clean_code": "Your code looks clean! 🎉" if analysis["bug_count"] == 0 else "Issues found:",
                "issues": []
            }

            if analysis["code_smells"]:
                analysis_summary["issues"].append({
                    "category": "Code Smells",
                    "details": analysis["code_smells"]
                })

            if analysis["coding_standard_violations"]:
                analysis_summary["issues"].append({
                    "category": "Coding Standard Violations",
                    "details": analysis["coding_standard_violations"]
                })

            if analysis["security_issues"]:
                analysis_summary["issues"].append({
                    "category": "Security Issues",
                    "details": analysis["security_issues"]
                })

            if analysis["unused_variables"]:
                analysis_summary["issues"].append({
                    "category": "Unused Variables",
                    "details": analysis["unused_variables"]
                })

            if analysis["indentation_issues"]:
                analysis_summary["issues"].append({
                    "category": "Indentation Issues",
                    "details": analysis["indentation_issues"]
                })

            if analysis["unused_imports"]:
                analysis_summary["issues"].append({
                    "category": "Unused Imports",
                    "details": analysis["unused_imports"]
                })

            if analysis["deprecated_rules"]:
                analysis_summary["issues"].append({
                    "category": "Deprecated Rules",
                    "details": [
                        f"{rule['ruleId']} → replaced by {', '.join(rule['replacedBy'])}" for rule in analysis["deprecated_rules"]
                    ]
                })
                
            execution_time = round(time.time() - start_time, 3)
            current, peak = tracemalloc.get_traced_memory()
            memory_usage_kb = round(peak / 1024, 2)
            tracemalloc.stop()

            analysis_summary["execution_time"] = execution_time
            analysis_summary["memory_usage_kb"] = memory_usage_kb

            return jsonify({
                "status": "success",
                "analysis": analysis_summary
            })

        checker = CodeQualityChecker(file_path, language)
        pylint_results = checker.run_pylint()
        bandit_results = checker.run_bandit()
        complexity_results = checker.check_cyclomatic_complexity()

        analysis = {
            "bug_count": len(pylint_results),
            "vulnerabilities": len(bandit_results.get("results", [])),
            "code_smells": [msg['message'] for msg in pylint_results if msg.get("type") == "refactor"],
            "coding_standard_violations": [msg['message'] for msg in pylint_results if msg.get("type") == "convention"],
            "cyclomatic_complexity": complexity_results,
            "security_issues": bandit_results.get("results", []),
            "indentation_issues": [msg['message'] for msg in pylint_results if msg.get("message").startswith("Bad indentation")],
            "unused_imports": [msg['message'] for msg in pylint_results if msg.get("message").startswith("Unused import")],
            "hardcoded_passwords": [
                msg.get("issue", "Unknown")
                for msg in bandit_results.get("results", [])
                if msg.get("issue") == "B105:hardcoded_password_string"
            ]
        }

        analysis_summary = {
            "clean_code": "Your code looks clean! 🎉" if all(value == 0 for key, value in analysis.items() if isinstance(value, int)) else "Issues found:",
            "issues": []
        }

        if analysis["bug_count"]:
            analysis_summary["issues"].append({
                "category": "Bugs",
                "details": [msg['message'] for msg in pylint_results]
            })

        if analysis["vulnerabilities"]:
            analysis_summary["issues"].append({
                "category": "Security Vulnerabilities",
                "details": [msg.get('issue', msg.get('test_id', 'Unknown')) for msg in bandit_results.get("results", [])]
            })

        if analysis["cyclomatic_complexity"]:
            analysis_summary["issues"].append({
                "category": "Cyclomatic Complexity",
                "details": [str(complexity_results)]
            })

        if analysis["indentation_issues"]:
            analysis_summary["issues"].append({
                "category": "Indentation Issues",
                "details": analysis["indentation_issues"]
            })

        if analysis["unused_imports"]:
            analysis_summary["issues"].append({
                "category": "Unused Imports",
                "details": analysis["unused_imports"]
            })

        if analysis["hardcoded_passwords"]:
            analysis_summary["issues"].append({
                "category": "Hardcoded Passwords",
                "details": analysis["hardcoded_passwords"]
            })

        execution_time = round(time.time() - start_time, 3)
        current, peak = tracemalloc.get_traced_memory()
        memory_usage_kb = round(peak / 1024, 2)
        tracemalloc.stop()

        analysis_summary["execution_time"] = execution_time
        analysis_summary["memory_usage_kb"] = memory_usage_kb

        
        return jsonify({
            "status": "success",
            "analysis": analysis_summary
        })

    except Exception as e:
        app.logger.error(f"Exception occurred: {str(e)}")
        return jsonify({"status": "error", "message": "Internal error"}), 500
    
def cleanup_old_uploads():
    while True:
        now = datetime.now()
        cutoff = now - timedelta(hours=1)

        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if os.path.isfile(file_path):
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_modified_time < cutoff:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting file {filename}: {e}")

        # Sleep for 10 minutes before next check
        time.sleep(600)

# Start background cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_uploads, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    app.run(debug=True)
