const BACKEND_URL = "http://192.168.9.253:8080";

const fieldsContainer = document.getElementById('fields-container');
const abbreviationsContainer = document.getElementById('abbreviations-container');
const fetchBtn = document.getElementById('fetch-options');
const generateBtn = document.getElementById('generate-btn');
const resultDiv = document.getElementById('result');
const warningBox = document.getElementById('warning-box');

// ---------------------------
// Cumulative length feature
// ---------------------------
const MIN_LENGTH = 14;
const MAX_LENGTH = 22;
const lengthStatusBox = document.getElementById('length-status');
const totalLengthSpan = document.getElementById('total-length');
const lengthMessage = document.getElementById('length-message');

let selectedOptions = {};   // { word: abbreviation }
let wordsOptionsData = {};
let descriptionValue = "";

// ---------------------------
// Render all fields from /fields endpoint
// ---------------------------
async function renderFields() {
    const res = await fetch(`${BACKEND_URL}/fields`);
    const data = await res.json();
    const fields = data.fields;

    fieldsContainer.innerHTML = "";

    for (const field in fields) {
        const fieldData = fields[field];

        const col = document.createElement('div');
        col.className = (field === "description") ? "col-12" : "col-md-6";
        const wrapper = document.createElement('div');
        wrapper.classList.add('mb-3');

        const label = document.createElement('label');
        label.classList.add('form-label');
        label.textContent = field.charAt(0).toUpperCase() + field.slice(1);
        wrapper.appendChild(label);

        if (fieldData.type === "select") {
            const select = document.createElement('select');
            select.classList.add('form-select');
            select.id = field;
            fieldData.options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt;
                select.appendChild(option);
            });
            wrapper.appendChild(select);
        } else {
            const input = document.createElement('input');
            input.type = "text";
            input.classList.add('form-control');
            input.id = field;
            input.placeholder = fieldData.description || `Enter ${field}`;
            wrapper.appendChild(input);
        }

        col.appendChild(wrapper);
        fieldsContainer.appendChild(col);
    }
}

// ---------------------------
// Fetch abbreviation options for description
// ---------------------------
fetchBtn.addEventListener('click', async () => {
    const descriptionInput = document.getElementById('description');
    const description = descriptionInput.value.trim();
    if (!description) return alert("Please enter a description.");

    if (description === descriptionValue && Object.keys(wordsOptionsData).length) return;
    descriptionValue = description;

    try {
        const res = await fetch(`${BACKEND_URL}/generate-options`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description })
        });
        const data = await res.json();
        wordsOptionsData = data.words_options;

        renderAbbreviationCards(wordsOptionsData);

        fetchBtn.disabled = true;
        warningBox.style.display = 'none';
        resultDiv.classList.add('d-none');
        generateBtn.disabled = true;
        if(lengthStatusBox) lengthStatusBox.classList.add('d-none');

    } catch (err) {
        console.error(err);
        alert("Error fetching abbreviation options.");
    }
});

// ---------------------------
// Render abbreviation cards
// ---------------------------
function renderAbbreviationCards(wordsOptions) {
    abbreviationsContainer.innerHTML = "";
    selectedOptions = {};  // reset previous selections

    for (const word in wordsOptions) {
        const col = document.createElement('div');
        col.className = "col-12 col-md-6 col-lg-4";

        const card = document.createElement('div');
        card.classList.add('option-card');

        const title = document.createElement('h5');
        title.textContent = word;
        card.appendChild(title);

        wordsOptions[word].forEach(opt => {
            const label = document.createElement('label');
            label.classList.add('option-label');

            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = word;
            radio.value = opt.value;
            radio.style.marginRight = '5px';
            if (opt.conflict) radio.dataset.conflict = "true";

            radio.addEventListener('change', () => {
                selectedOptions[word] = opt.value;
                checkConflicts();
                updateTotalLength();   // ✅ New: cumulative length
            });

            const optionText = document.createElement('span');
            optionText.classList.add('option-text');
            optionText.textContent = opt.value;

            const labelsContainer = document.createElement('span');
            labelsContainer.classList.add('option-labels');

            if (opt.in_use) {
                const inUse = document.createElement('span');
                inUse.textContent = 'in use';
                inUse.classList.add('in-use');
                labelsContainer.appendChild(inUse);
            }
            if (opt.conflict) {
                const conflict = document.createElement('span');
                conflict.textContent = 'conflict';
                conflict.classList.add('conflict');
                labelsContainer.appendChild(conflict);
            }

            label.appendChild(radio);
            label.appendChild(optionText);
            label.appendChild(labelsContainer);
            card.appendChild(label);
        });

        col.appendChild(card);
        abbreviationsContainer.appendChild(col);
    }
}

// ---------------------------
// Check for conflicts
// ---------------------------
function checkConflicts() {
    let conflictExists = false;

    for (const word in wordsOptionsData) {
        const radios = document.getElementsByName(word);
        radios.forEach(r => {
            if (r.checked && r.dataset.conflict === "true") {
                conflictExists = true;
                warningBox.textContent =
                    `Conflict detected: abbreviation "${r.value}" for word "${word}" is already in use.`;
                warningBox.style.display = 'block';
            }
        });
    }

    if (!conflictExists) warningBox.style.display = 'none';
}

// ---------------------------
// Update cumulative length
// ---------------------------
function updateTotalLength() {
    let totalLength = 0;

    Object.values(selectedOptions).forEach(val => {
        if (val) totalLength += val.length;
    });

    if(lengthStatusBox){
        lengthStatusBox.classList.remove('d-none');
        totalLengthSpan.textContent = totalLength;

        if (totalLength < MIN_LENGTH) {
            lengthStatusBox.className = "length-box invalid";
            lengthMessage.textContent = `Minimum ${MIN_LENGTH} required (${MIN_LENGTH - totalLength} more needed)`;
        } else if (totalLength > MAX_LENGTH) {
            lengthStatusBox.className = "length-box invalid";
            lengthMessage.textContent = `Maximum ${MAX_LENGTH} allowed (reduce ${totalLength - MAX_LENGTH})`;
        } else {
            lengthStatusBox.className = "length-box valid";
            lengthMessage.textContent = "Length within allowed range ✔";
        }
    }

    updateGenerateButtonState();
}

// ---------------------------
// Enable/disable generate button
// ---------------------------
function updateGenerateButtonState() {
    const totalWords = Object.keys(wordsOptionsData).length;
    const selectedCount = Object.keys(selectedOptions).length;

    let conflictExists = false;
    for (const word in wordsOptionsData) {
        const radios = document.getElementsByName(word);
        radios.forEach(r => {
            if (r.checked && r.dataset.conflict === "true") conflictExists = true;
        });
    }

    // ✅ Disable generate button if not all selected OR conflict OR length out of bounds
    let totalLength = 0;
    Object.values(selectedOptions).forEach(val => { if(val) totalLength += val.length; });
    const lengthInvalid = totalLength < MIN_LENGTH || totalLength > MAX_LENGTH;

    generateBtn.disabled = selectedCount !== totalWords || conflictExists || totalWords === 0 || lengthInvalid;
}



// ---------------------------
// Generate variable name
// ---------------------------
generateBtn.addEventListener('click', async () => {
    if (Object.keys(selectedOptions).length === 0) {
        alert("Please select abbreviation for each word.");
        return;
    }

    const payload = {};

    // Collect all fields including description
    document.querySelectorAll('#fields-container input, #fields-container select').forEach(el => {
        if (el.id === 'description') {
            payload["description_user"] = el.value.trim();   // ✅ raw user description
        } else {
            payload[el.id] = el.value;
        }
    });

    // Send selected abbreviations separately
    payload["description"] = { ...selectedOptions };  // ✅ abbreviation dict

    try {
        const res = await fetch(`${BACKEND_URL}/generate-variable-name`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errorText = await res.text();
            alert("Backend error: " + errorText);
            return;
        }

        const data = await res.json();

        // Show generated name
        resultDiv.classList.remove('d-none', 'alert-danger');
        resultDiv.classList.add('alert-success');
        resultDiv.innerHTML = `
            <strong>Generated Variable Name: </strong>
            <span style="font-size:22px;font-weight:bold;color:#4B0082;">
                ${data.variable_name}
            </span>
        `;

        // Show warnings if any
        if (data.warnings && data.warnings.length > 0) {
            warningBox.innerHTML = data.warnings
                .map(w => `<div class="alert alert-warning mt-2">${w}</div>`)
                .join("");
            warningBox.style.display = "block";
        } else {
            warningBox.style.display = "none";
            warningBox.innerHTML = "";
        }

    } catch (err) {
        console.error(err);
        resultDiv.classList.remove('d-none', 'alert-success');
        resultDiv.classList.add('alert-danger');
        resultDiv.textContent = "Error generating variable name.";
    }
});
// ---------------------------
// Reset fetch button when description changes
// ---------------------------
fieldsContainer.addEventListener('input', e => {
    if (e.target.id === 'description') fetchBtn.disabled = false;
});

// Initial render
renderFields();