# 🛠️ Code Quality Checker and Optimization Tool

A developer-friendly tool designed to **analyze, optimize, and enhance code quality** across multiple programming languages like **Python** and **JavaScript**. It helps improve code **performance**, **readability**, and **maintainability** through detailed insights and recommendations.

---

## 📌 Features

- ✅ Upload code files (Python, JavaScript)
- ✅ Detect bugs, security issues, and bad practices
- ✅ Analyze code complexity and maintainability
- ✅ Provide optimized code suggestions
- ✅ View performance metrics (execution time, memory usage)
- ✅ Easy-to-use interface for quick feedback

---

## 🧠 How It Works

1. **Upload Code**: User selects a `.py` or `.js` file for analysis.
2. **Select Mode**: Choose between **Code Optimization** or **Quality Analysis**.
3. **Processing**:
   - In *Optimization Mode*: Tool suggests improvements to boost speed and reduce memory usage.
   - In *Analysis Mode*: Tool identifies code smells, bugs, and potential vulnerabilities.
4. **Results Displayed**:
   - Optimized version of the code (if selected)
   - Metrics: execution time, memory usage
   - Issues found, suggestions for improvement

---

## 🛠️ Technologies Used

| Feature              | Technology                       |
|----------------------|----------------------------------|
| Backend              | Python                           |
| Code Parsing & Analysis | `ast`, `pylint`, `radon`, `bandit`, `esprima` (for JS) |
| UI Framework         | Flask or Tkinter (based on version) |
| Supported Languages  | Python, JavaScript               |

---

## 🚀 How to Run

```bash
# Clone the repository
git clone https://github.com/your-username/Code-Quality-Checker-and-Optimization-Tool.git
cd Code-Quality-Checker-and-Optimization-Tool

# Run the Python application
python app.py
