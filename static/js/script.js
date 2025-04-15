document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const inputMethod = document.getElementsByName('input-method');
    const dropdownInputs = document.getElementById('dropdown-inputs');
    const urlInput = document.getElementById('url-input');
    const fetchButton = document.getElementById('fetch-button');
    const loadingIndicator = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const resultContainer = document.getElementById('result-container');
    const talmudTextContainer = document.getElementById('talmud-text-container');
    const selectAllButton = document.getElementById('select-all');
    
    // Input method toggle
    inputMethod.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'dropdown') {
                dropdownInputs.style.display = 'flex';
                urlInput.style.display = 'none';
            } else {
                dropdownInputs.style.display = 'none';
                urlInput.style.display = 'block';
            }
        });
    });
    
    // Select all text functionality
    selectAllButton.addEventListener('click', function() {
        selectTextInElement(talmudTextContainer);
    });
    
    // Fetch button click handler
    fetchButton.addEventListener('click', function() {
        fetchTalmudText();
    });
    
    // Fetch text from server
    function fetchTalmudText() {
        // Show loading, hide results
        loadingIndicator.style.display = 'block';
        errorMessage.style.display = 'none';
        resultContainer.style.display = 'none';
        
        // Determine which input method is active
        const activeMethod = document.querySelector('input[name="input-method"]:checked').value;
        let requestData = {
            input_method: activeMethod
        };
        
        // Get input data based on method
        if (activeMethod === 'dropdown') {
            requestData.tractate = document.getElementById('tractate').value;
            requestData.page = document.getElementById('page').value;
            requestData.section = document.getElementById('section').value;
        } else {
            requestData.url = document.getElementById('sefaria-url').value;
            if (!requestData.url) {
                showError('Please enter a valid Sefaria URL');
                return;
            }
        }
        
        // Send request to server
        fetch('/fetch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.style.display = 'none';
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            displayTalmudText(data);
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            showError('An error occurred while fetching the text. Please try again.');
            console.error('Error:', error);
        });
    }
    
    // Display error message
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        loadingIndicator.style.display = 'none';
        resultContainer.style.display = 'none';
    }
    
    // Display talmud text
    function displayTalmudText(data) {
        // Clear previous content
        talmudTextContainer.innerHTML = '';
        
        // Add span information
        if (data.span) {
            const spanInfo = document.createElement('div');
            spanInfo.className = 'span-info';
            spanInfo.textContent = data.span;
            talmudTextContainer.appendChild(spanInfo);
        }
        
        // Process each section
        if (data.sections && data.sections.length > 0) {
            data.sections.forEach((section, index) => {
                const sectionDiv = document.createElement('div');
                sectionDiv.className = 'talmud-section';
                
                // Add Hebrew text
                if (section.hebrew && section.hebrew.length > 0) {
                    const hebrewDiv = document.createElement('div');
                    hebrewDiv.className = 'hebrew-text';
                    
                    section.hebrew.forEach(sentence => {
                        const p = document.createElement('p');
                        p.innerHTML = sentence;
                        hebrewDiv.appendChild(p);
                    });
                    
                    sectionDiv.appendChild(hebrewDiv);
                }
                
                // Add English text
                if (section.english && section.english.length > 0) {
                    const englishDiv = document.createElement('div');
                    englishDiv.className = 'english-text';
                    
                    section.english.forEach(sentence => {
                        const p = document.createElement('p');
                        p.innerHTML = sentence;
                        englishDiv.appendChild(p);
                    });
                    
                    sectionDiv.appendChild(englishDiv);
                }
                
                talmudTextContainer.appendChild(sectionDiv);
                
                // Add separator between sections (except for the last one)
                if (index < data.sections.length - 1) {
                    const separator = document.createElement('hr');
                    separator.className = 'section-separator';
                    talmudTextContainer.appendChild(separator);
                }
            });
            
            // Show the result container
            resultContainer.style.display = 'block';
        } else {
            showError('No text found for the given reference.');
        }
    }
    
    // Function to select all text in an element
    function selectTextInElement(element) {
        const range = document.createRange();
        range.selectNodeContents(element);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }
});
