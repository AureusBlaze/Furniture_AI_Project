const uploadSection = document.getElementById('upload-section');
const fileInput = document.getElementById('file-input');
const preview = document.getElementById('preview');
const uploadPlaceholder = document.getElementById('upload-placeholder');
const analyzeBtn = document.getElementById('analyze-btn');
const loader = document.getElementById('loader');
const results = document.getElementById('results');
const analysisGrid = document.getElementById('analysis-grid');
const furnitureGrid = document.getElementById('furniture-grid');
const filterBar = document.getElementById('filter-bar');
const selectedPanel = document.getElementById('selected-panel');
const selectedItems = document.getElementById('selected-items');
const selectedCount = document.getElementById('selected-count');
const saveBtn = document.getElementById('save-btn');

let selectedFile = null;
let allFurniture = [];
let currentFilter = 'all';
let selectedFurniture = [];

uploadSection.addEventListener('click', () => fileInput.click());

uploadSection.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadSection.classList.add('dragover');
});

uploadSection.addEventListener('dragleave', () => {
    uploadSection.classList.remove('dragover');
});

uploadSection.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadSection.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFile(file);
    }
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

function handleFile(file) {
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = 'block';
        uploadPlaceholder.style.display = 'none';
        uploadSection.classList.add('has-image');
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    loader.style.display = 'block';
    results.style.display = 'none';
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Analysis failed');
        }

        const data = await response.json();
        if (data.error) throw new Error(data.error);
        displayResults(data);
    } catch (error) {
        alert('Error analyzing image: ' + error.message);
    } finally {
        loader.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

function displayResults(data) {
    const analysis = data.room_analysis || {};
    allFurniture = data.all_furniture || [];

    const dominantColorsData = data.dominant_colors || {};
    let dominantColors = [];
    if (Array.isArray(dominantColorsData)) {
        dominantColors = dominantColorsData;
    } else if (dominantColorsData && Array.isArray(dominantColorsData.colors)) {
        dominantColors = dominantColorsData.colors;
    }

    const lighting = data.lighting_analysis || {};
    const composition = data.composition || {};
    const roomType = Array.isArray(data.room_type) ? data.room_type : [];
    const materials = Array.isArray(data.materials) ? data.materials : [];
    const mood = Array.isArray(data.mood) ? data.mood : [];

    const colorDots = dominantColors.map(c =>
        `<div class="color-dot-large" style="background:${c.hex}; width:40px; height:40px; border-radius:50%; display:inline-block; margin:3px;" title="${c.name} (${c.percentage}%)"></div>`
    ).join('');

    const colorList = dominantColors.map(c =>
        `<div style="display:flex; align-items:center; gap:10px; margin:5px 0;">
            <div style="width:20px; height:20px; background:${c.hex}; border-radius:4px;"></div>
            <span>${c.name} - ${c.hex} (${c.percentage}%)</span>
        </div>`
    ).join('');

    const roomTypeLabel = roomType[0]?.label || 'Unknown';
    const materialsLabel = materials.slice(0, 3).map(m => m.label.split(' ').slice(0, 2).join(' ')).join(', ');
    const moodLabel = mood[0]?.label || 'Unknown';

    analysisGrid.innerHTML = `
        <div class="analysis-item">
            <h3>Room Type</h3>
            <p>${formatLabel(roomTypeLabel)}</p>
        </div>
        <div class="analysis-item">
            <h3>Style</h3>
            <p>${formatLabel(analysis.style)}</p>
        </div>
        <div class="analysis-item">
            <h3>Color Palette</h3>
            <p>${formatLabel(analysis.color_palette)}</p>
        </div>
        <div class="analysis-item">
            <h3>Lighting</h3>
            <p>${formatLabel(analysis.lighting)}</p>
        </div>
        <div class="analysis-item">
            <h3>Space</h3>
            <p>${formatLabel(analysis.space)}</p>
        </div>
        <div class="analysis-item">
            <h3>Mood</h3>
            <p>${formatLabel(moodLabel)}</p>
        </div>
        <div class="analysis-item">
            <h3>Materials</h3>
            <p>${materialsLabel || 'N/A'}</p>
        </div>
        <div class="analysis-item">
            <h3>Dominant Colors</h3>
            <p><strong>Temperature:</strong> ${dominantColorsData.temperature || dominantColorsData.color_temperature || 'N/A'}</p>
            <p><strong>Saturation:</strong> ${dominantColorsData.saturation || 'N/A'}</p>
            <div style="margin-bottom:10px; margin-top:10px;">${colorDots}</div>
            ${colorList}
        </div>
        <div class="analysis-item">
            <h3>Lighting Analysis</h3>
            <p><strong>Brightness:</strong> ${lighting.brightness_level || 'N/A'} (${lighting.brightness_value || 0})</p>
            <p><strong>Contrast:</strong> ${lighting.contrast_level || 'N/A'}</p>
            <p><strong>Exposure:</strong> ${lighting.exposure || 'N/A'}</p>
        </div>
        <div class="analysis-item">
            <h3>Composition</h3>
            <p><strong>Aspect Ratio:</strong> ${composition.aspect_ratio || 'N/A'}</p>
            <p><strong>Orientation:</strong> ${composition.orientation || 'N/A'}</p>
            <p><strong>Complexity:</strong> ${composition.complexity || 'N/A'}</p>
            <p><strong>Symmetry:</strong> ${composition.is_symmetrical ? 'Yes' : 'No'} (${composition.symmetry_score || 0})</p>
        </div>
    `;

    const types = [...new Set(allFurniture.map(item => item.type))];
    filterBar.innerHTML = `
        <button class="filter-btn active" data-filter="all">All</button>
        ${types.map(type => `<button class="filter-btn" data-filter="${type}">${type.charAt(0).toUpperCase() + type.slice(1)}s</button>`).join('')}
    `;

    filterBar.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            filterBar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderFurniture();
        });
    });

    renderFurniture();
    results.style.display = 'block';
}

function renderFurniture() {
    const filtered = currentFilter === 'all'
        ? allFurniture
        : allFurniture.filter(item => item.type === currentFilter);

    furnitureGrid.innerHTML = filtered.map(item => {
        const isSelected = selectedFurniture.some(s => s.id === item.id);
        return `
            <div class="furniture-card ${isSelected ? 'selected' : ''}" data-id="${item.id}">
                <h3>${item.name}</h3>
                <p class="type">${item.type}</p>
                <div class="details">
                    <p><strong>Style:</strong> ${item.style}</p>
                    <p><strong>Size:</strong> ${item.size}</p>
                    <p><strong>Colors:</strong> ${item.colors.join(', ')}</p>
                </div>
                <p class="price">$${item.price}</p>
                <span class="match-score">Match: ${item.match_score}%</span>
                <br>
                <button class="btn btn-small ${isSelected ? 'btn-selected' : ''}" onclick="toggleSelect('${item.id}')">
                    ${isSelected ? 'Remove' : 'Select'}
                </button>
            </div>
        `;
    }).join('');
}

function toggleSelect(id) {
    const item = allFurniture.find(f => f.id === id);
    const index = selectedFurniture.findIndex(s => s.id === id);

    if (index > -1) {
        selectedFurniture.splice(index, 1);
    } else {
        selectedFurniture.push(item);
    }

    updateSelectedPanel();
    renderFurniture();
}

function updateSelectedPanel() {
    if (selectedFurniture.length > 0) {
        selectedPanel.style.display = 'block';
        selectedCount.textContent = `${selectedFurniture.length} item${selectedFurniture.length > 1 ? 's' : ''} selected`;
        selectedItems.innerHTML = selectedFurniture.map(item => `
            <div class="selected-item">
                ${item.name}
                <button class="remove-btn" onclick="toggleSelect('${item.id}')">×</button>
            </div>
        `).join('');
    } else {
        selectedPanel.style.display = 'none';
    }
}

saveBtn.addEventListener('click', () => {
    const data = {
        selected_furniture: selectedFurniture.map(item => ({
            id: item.id,
            name: item.name,
            type: item.type,
            price: item.price
        })),
        total_price: selectedFurniture.reduce((sum, item) => sum + item.price, 0)
    };

    console.log('Saved selection:', data);
    alert(`Saved ${selectedFurniture.length} items! Total: $${data.total_price}`);
});

function formatLabel(text) {
    if (!text) return 'Unknown';
    return text.replace('room', '').trim().split(' ').map(
        word => word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}
