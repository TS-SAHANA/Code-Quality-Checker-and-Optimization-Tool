document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("code-quality-form");
    const fileInput = document.getElementById("file-upload");
    const fileNameDisplay = document.getElementById("file-name");

    const spinner = document.getElementById("loading-spinner");
    const resultsContainer = document.getElementById("results-container");
    const optimizedCodeBlock = document.getElementById("optimized-code");
    const analysisSection = document.getElementById("analysis-section");
    const optimizationSection = document.getElementById("optimization-section");
    const downloadButton = document.getElementById("download-button");
    const analysisResults = document.getElementById("analysis-results");

    const tileToggle = document.querySelector('.tile-toggle');
    const optimizeOption = document.getElementById('optimize-option');
    const analyzeOption = document.getElementById('analyze-option');
    const selectedIndicator = document.querySelector('.selected-indicator');

    let selectedFeature = 'optimize'; // Default mode

    // === Initial UI Setup ===
    optimizeOption.classList.add('selected');
    selectedIndicator.style.left = '0';
    optimizeOption.style.color = 'white';
    analyzeOption.style.color = '#333';

    // === Toggle between Optimization and Analysis ===
    tileToggle.addEventListener('click', (e) => {
        if (e.target === optimizeOption) {
            selectedFeature = 'optimize';
            optimizeOption.classList.add('selected');
            analyzeOption.classList.remove('selected');
            selectedIndicator.style.left = '0';
            optimizeOption.style.color = 'white';
            analyzeOption.style.color = '#333';
            console.log('Code Optimization selected');
        } else if (e.target === analyzeOption) {
            selectedFeature = 'analyze';
            analyzeOption.classList.add('selected');
            optimizeOption.classList.remove('selected');
            selectedIndicator.style.left = '50%';
            analyzeOption.style.color = 'white';
            optimizeOption.style.color = '#333';
            console.log('Code Quality Analysis selected');
        }
    });

    // === Display File Name ===
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = "Selected file: " + fileInput.files[0].name;
            fileNameDisplay.style.color = "white";
        } else {
            fileNameDisplay.textContent = "";
        }
    });

    // === Handle Form Submit ===
    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const file = fileInput.files[0];
        if (!file || !selectedFeature) {
            alert("Please select both a feature and a file.");
            return;
        }

        // Reset UI state
        resultsContainer.classList.remove("show");
        optimizationSection.style.display = "none";
        analysisSection.style.display = "none";
        optimizedCodeBlock.textContent = "";
        analysisResults.innerHTML = "";
        downloadButton.style.display = "none";
        spinner.style.display = "block";

        const formData = new FormData();
        formData.append("file", file);

        const endpoint = selectedFeature === "analyze" ? "/analyze_code_quality" : "/check_code_quality";

        fetch(endpoint, {
            method: "POST",
            body: formData
        })
        .then(response => {
            spinner.style.display = "none";
            if (!response.ok) {
                throw new Error("Server returned an error: " + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log("API response:", data);
            if (data.status === "success") {
                resultsContainer.classList.add("show");

                if (selectedFeature === "optimize") {
                    optimizationSection.style.display = "block";
                    optimizedCodeBlock.textContent = data.optimized_code || "No changes detected.";

                    // Enable download button
                    downloadButton.style.display = "inline-block";
                    downloadButton.onclick = () => {
                        const link = document.createElement("a");
                        link.href = data.download_url;
                        link.download = file.name.startsWith("optimized_") ? file.name : `optimized_${file.name}`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    };

                    const performanceSection = document.getElementById("performance-metrics");
                    const execTime = document.getElementById("execution-time");
                    const memoryUsage = document.getElementById("memory-usage");

                    // Show and update performance metrics
                    if (data.execution_time !== undefined && data.memory_usage_kb !== undefined) {
                        performanceSection.style.display = "block";
                        execTime.textContent = data.execution_time;
                        memoryUsage.textContent = data.memory_usage_kb;
                    } else if (data.analysis && data.analysis.execution_time !== undefined) {
                        performanceSection.style.display = "block";
                        execTime.textContent = data.analysis.execution_time;
                        memoryUsage.textContent = data.analysis.memory_usage_kb;
                    } else {
                        performanceSection.style.display = "none";
                    }

                }

                if (selectedFeature === "analyze") {
                    analysisSection.style.display = "block";
                    analysisResults.innerHTML = formatAnalysisResults(data.analysis || {});
                }
            } else {
                alert("Error: " + (data.message || "Something went wrong."));
            }
        })
        .catch(error => {
            spinner.style.display = "none";
            console.error("Error:", error);
            alert("An error occurred: " + error.message);
        });
    });

    // === Render Analysis Summary ===
    function formatAnalysisResults(analysis) {
        let html = "";

        if (analysis.clean_code) {
            html += `<p><strong>${analysis.clean_code}</strong></p>`;
        }

        if (Array.isArray(analysis.issues)) {
            const categoryIcons = {
                "Bugs": "🐞",
                "Security Vulnerabilities": "🔐",
                "Cyclomatic Complexity": "🧠",
                "Indentation Issues": "📏",
                "Unused Imports": "📦",
                "Hardcoded Passwords": "🔑"
            };

            analysis.issues.forEach((issue) => {
                const icon = categoryIcons[issue.category] || "📌";

                html += `
                    <button class="accordion">${icon} ${issue.category}</button>
                    <div class="panel">
                        <ul>
                            ${issue.details.map(detail => {
                                if (issue.category === "Cyclomatic Complexity") {
                                    return `<li><pre class="cyclomatic-complexity">${JSON.stringify(detail, null, 2)}</pre></li>`;
                                } else {
                                    return `<li>${detail}</li>`;
                                }
                            }).join("")}
                        </ul>
                    </div>`;
            });
        }

        if (!html) {
            html = "<p>No issues found. Your code looks clean! 🎉</p>";
        }

        return html;
    }
});

// === Handle Accordion Toggle ===
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("accordion")) {
        e.target.classList.toggle("active");

        const panel = e.target.nextElementSibling;
        panel.classList.toggle("active-panel");
    }
});

document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      const target = document.getElementById(targetId);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
  
// /* Codezee, Codezilla, CodePulse */