let groupsData = [];
let boxplotsData = null;
let mainFiles = [];
let competitorFiles = [];
let characteristicsData = [];

// Определяем префикс API на основе текущего URL
function getApiPrefix() {
    const path = window.location.pathname;
    if (path.startsWith('/akvilon')) {
        return '/akvilon';
    }
    return '';
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация...');
    initFileUploads();
    initButtons();
});

function initFileUploads() {
    const mainInput = document.getElementById('main_files');
    const competitorInput = document.getElementById('competitor_files');
    const mainUploadArea = document.getElementById('main_upload_area');
    const competitorUploadArea = document.getElementById('competitor_upload_area');
    
    if (!mainInput || !competitorInput || !mainUploadArea || !competitorUploadArea) {
        console.error('Не найдены элементы для загрузки файлов');
        return;
    }
    
    // Инициализируем классы для начального состояния
    mainUploadArea.classList.add('files-not-loaded');
    competitorUploadArea.classList.add('files-not-loaded');
    
    // Обновляем превью для начального состояния (пустые массивы)
    updateFilesPreview('main', mainFiles);
    updateFilesPreview('competitor', competitorFiles);
    
    // Обработчик клика на область загрузки для основного ЖК
    mainUploadArea.addEventListener('click', (e) => {
        // Не открываем диалог, если клик был на кнопке удаления или на самом файле
        if (e.target.closest('.file-preview-item') || e.target.closest('.file-remove')) {
            return;
        }
        // Не открываем диалог, если клик был на самом input
        if (e.target === mainInput) {
            return;
        }
        console.log('Клик на область загрузки основного ЖК');
        mainInput.click();
    });
    
    // Обработчики для основного ЖК
    mainInput.addEventListener('change', (e) => {
        console.log('Изменение файлов основного ЖК, выбрано файлов:', e.target.files.length);
        const selectedFiles = Array.from(e.target.files);
        console.log('Выбранные файлы:', selectedFiles.map(f => f.name));
        
        // Добавляем все новые файлы
        selectedFiles.forEach(file => {
            // Проверяем, что файл еще не добавлен
            const exists = mainFiles.some(existingFile => 
                existingFile.name === file.name && existingFile.size === file.size
            );
            if (!exists) {
                mainFiles.push(file);
                console.log('Добавлен файл:', file.name);
            }
        });
        
        console.log('Всего основных файлов после добавления:', mainFiles.length);
        
        // Обновляем превью
        updateFilesPreview('main', mainFiles);
        
        // Обновляем input с учетом всех файлов
        updateInputFiles('main_files', mainFiles);
    });
    setupDragAndDrop(mainUploadArea, 'main');
    
    // Обработчик клика на область загрузки для конкурентов
    competitorUploadArea.addEventListener('click', (e) => {
        // Не открываем диалог, если клик был на кнопке удаления или на самом файле
        if (e.target.closest('.file-preview-item') || e.target.closest('.file-remove')) {
            return;
        }
        // Не открываем диалог, если клик был на самом input
        if (e.target === competitorInput) {
            return;
        }
        console.log('Клик на область загрузки конкурентов');
        competitorInput.click();
    });
    
    // Обработчики для конкурентов
    competitorInput.addEventListener('change', (e) => {
        console.log('Изменение файлов конкурентов, выбрано файлов:', e.target.files.length);
        const selectedFiles = Array.from(e.target.files);
        console.log('Выбранные файлы:', selectedFiles.map(f => f.name));
        
        // Добавляем все новые файлы
        selectedFiles.forEach(file => {
            // Проверяем, что файл еще не добавлен
            const exists = competitorFiles.some(existingFile => 
                existingFile.name === file.name && existingFile.size === file.size
            );
            if (!exists) {
                competitorFiles.push(file);
                console.log('Добавлен файл:', file.name);
            }
        });
        
        console.log('Всего файлов конкурентов после добавления:', competitorFiles.length);
        
        // Обновляем превью
        updateFilesPreview('competitor', competitorFiles);
        
        // Обновляем input с учетом всех файлов
        updateInputFiles('competitor_files', competitorFiles);
    });
    setupDragAndDrop(competitorUploadArea, 'competitor');
}

function setupDragAndDrop(uploadArea, type) {
    const input = type === 'main' ? document.getElementById('main_files') : document.getElementById('competitor_files');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files).filter(file => file.name.endsWith('.csv'));
        if (files.length > 0) {
            handleFiles(files, type);
            // Обновляем input для совместимости
            const dataTransfer = new DataTransfer();
            const currentFiles = type === 'main' ? mainFiles : competitorFiles;
            [...currentFiles, ...files].forEach(file => dataTransfer.items.add(file));
            input.files = dataTransfer.files;
        }
    });
}

// Эта функция теперь не используется напрямую, но оставлена для drag-and-drop
function handleFiles(files, type) {
    const fileArray = Array.from(files);
    console.log(`Обработка файлов для ${type}:`, fileArray.length, 'файлов');
    
    if (type === 'main') {
        fileArray.forEach(file => {
            const exists = mainFiles.some(existingFile => 
                existingFile.name === file.name && existingFile.size === file.size
            );
            if (!exists) {
                mainFiles.push(file);
            }
        });
        console.log('Всего основных файлов:', mainFiles.length);
        updateFilesPreview('main', mainFiles);
        updateInputFiles('main_files', mainFiles);
    } else {
        fileArray.forEach(file => {
            const exists = competitorFiles.some(existingFile => 
                existingFile.name === file.name && existingFile.size === file.size
            );
            if (!exists) {
                competitorFiles.push(file);
            }
        });
        console.log('Всего файлов конкурентов:', competitorFiles.length);
        updateFilesPreview('competitor', competitorFiles);
        updateInputFiles('competitor_files', competitorFiles);
    }
}

function updateFilesPreview(type, files) {
    console.log(`Обновление превью для ${type}, файлов:`, files.length);
    
    const previewContainer = type === 'main' 
        ? document.getElementById('main_files_preview')
        : document.getElementById('competitor_files_preview');
    const uploadArea = type === 'main'
        ? document.getElementById('main_upload_area')
        : document.getElementById('competitor_upload_area');
    
    if (!previewContainer) {
        console.error(`Не найден контейнер превью для ${type}`);
        return;
    }
    
    if (!uploadArea) {
        console.error(`Не найдена область загрузки для ${type}`);
        return;
    }
    
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    
    previewContainer.innerHTML = '';
    
    // Управляем классом для скрытия/показа текста "Файлы не загружены"
    if (files.length > 0) {
        uploadArea.classList.add('files-loaded');
        uploadArea.classList.remove('files-not-loaded');
        
        // Обновляем placeholder, если есть файлы
        if (placeholder) {
            const p = placeholder.querySelector('p');
            if (p) {
                p.textContent = `${files.length} файл(ов) загружено`;
            }
        }
        
        files.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'file-preview-item';
            item.innerHTML = `
                <span class="file-name" title="${file.name}">${file.name}</span>
                <button class="file-remove" data-type="${type}" data-index="${index}" title="Удалить">×</button>
            `;
            previewContainer.appendChild(item);
        });
        
        console.log(`Превью обновлено, добавлено ${files.length} элементов`);
    } else {
        uploadArea.classList.remove('files-loaded');
        uploadArea.classList.add('files-not-loaded');
        
        // Восстанавливаем оригинальный placeholder
        if (placeholder) {
            const p = placeholder.querySelector('p');
            if (p) {
                p.innerHTML = 'Перетащите файлы сюда<br>или нажмите для выбора';
            }
        }
    }
    
    // Обработчик удаления файла
    previewContainer.querySelectorAll('.file-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Предотвращаем всплытие события
            const fileType = e.target.dataset.type;
            const fileIndex = parseInt(e.target.dataset.index);
            
            if (fileType === 'main') {
                mainFiles.splice(fileIndex, 1);
                updateFilesPreview('main', mainFiles);
                updateInputFiles('main_files', mainFiles);
            } else {
                competitorFiles.splice(fileIndex, 1);
                updateFilesPreview('competitor', competitorFiles);
                updateInputFiles('competitor_files', competitorFiles);
            }
        });
    });
}

function updateInputFiles(inputId, files) {
    const input = document.getElementById(inputId);
    const dataTransfer = new DataTransfer();
    files.forEach(file => dataTransfer.items.add(file));
    input.files = dataTransfer.files;
}

function initButtons() {
    const createGroupsBtn = document.getElementById('createGroupsBtn');
    
    if (!createGroupsBtn) {
        console.error('Кнопка createGroupsBtn не найдена!');
        return;
    }
    
    // Обработчик создания групп
    createGroupsBtn.addEventListener('click', async () => {
        console.log('Клик на кнопку "Создать группы"');
        console.log('Основных файлов:', mainFiles.length);
        console.log('Файлов конкурентов:', competitorFiles.length);
        
        if (mainFiles.length === 0) {
            showError('Пожалуйста, загрузите хотя бы один файл основного ЖК');
            return;
        }
        
        showLoading(true);
        hideError();
        
        try {
            const formData = new FormData();
            
            // Добавляем все файлы основного ЖК
            mainFiles.forEach(file => {
                formData.append('main_file', file);
                console.log('Добавлен основной файл:', file.name);
            });
            
            // Добавляем все файлы конкурентов
            competitorFiles.forEach(file => {
                formData.append('competitor_files', file);
                console.log('Добавлен файл конкурента:', file.name);
            });
            
            const apiPrefix = getApiPrefix();
            console.log('Отправка запроса на:', `${apiPrefix}/api/create_groups`);
            const response = await fetch(`${apiPrefix}/api/create_groups`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Ошибка при создании групп');
            }
            
        groupsData = data.groups;
        boxplotsData = data.boxplot || null;
        characteristicsData = data.characteristics || [];
        
        // Определяем режим группировки по умолчанию
        const groupByCharacteristicsRadio = document.getElementById('groupByCharacteristics');
        const groupByTypeRadio = document.getElementById('groupByType');
        const groupByVisualizationRadio = document.getElementById('groupByVisualization');
        const groupByObjectRadio = document.getElementById('groupByObject');
        let groupingMode = 'characteristics';
        if (groupByCharacteristicsRadio && groupByCharacteristicsRadio.checked) {
            groupingMode = 'characteristics';
        } else if (groupByVisualizationRadio && groupByVisualizationRadio.checked) {
            groupingMode = 'visualization';
        } else if (groupByTypeRadio && groupByTypeRadio.checked) {
            groupingMode = 'type';
        } else if (groupByObjectRadio && groupByObjectRadio.checked) {
            groupingMode = 'object';
        }
        displayGroups(groupsData, groupingMode);
        
        showLoading(false);
            
        } catch (error) {
            console.error('Ошибка при создании групп:', error);
            showError(error.message);
            showLoading(false);
        }
    });
    
    // Обработчик переключателя группировки
    const groupByObjectRadio = document.getElementById('groupByObject');
    const groupByTypeRadio = document.getElementById('groupByType');
    const groupByVisualizationRadio = document.getElementById('groupByVisualization');
    const groupByCharacteristicsRadio = document.getElementById('groupByCharacteristics');
    
    if (groupByObjectRadio && groupByTypeRadio && groupByVisualizationRadio && groupByCharacteristicsRadio) {
        const handleGroupingChange = () => {
            if (groupsData.length > 0 || boxplotsData || characteristicsData.length > 0) {
                let groupingMode = 'characteristics';
                if (groupByCharacteristicsRadio.checked) {
                    groupingMode = 'characteristics';
                } else if (groupByVisualizationRadio.checked) {
                    groupingMode = 'visualization';
                } else if (groupByTypeRadio.checked) {
                    groupingMode = 'type';
                } else if (groupByObjectRadio.checked) {
                    groupingMode = 'object';
                }
                displayGroups(groupsData, groupingMode);
            }
        };
        
        groupByObjectRadio.addEventListener('change', handleGroupingChange);
        groupByTypeRadio.addEventListener('change', handleGroupingChange);
        groupByVisualizationRadio.addEventListener('change', handleGroupingChange);
        groupByCharacteristicsRadio.addEventListener('change', handleGroupingChange);
    }
}

// Порядок сортировки типов площади (единый формат после нормализации)
// Порядок: XS (Студия) -> 1к -> S (2Евро) -> 2к -> M (3Евро) -> 3к -> L (4Евро) -> 4к -> 5к -> 6к и т.д.
const AREA_TYPE_ORDER = [
    'XS (Студия)',
    '1к',
    'S (2Евро)',
    '2к',
    'M (3Евро)',
    '3к',
    'L (4Евро)',
    '4к',
    '5к',
    '6к',
    '7к',
    '8к'
];

// Функция для получения порядка сортировки типа площади
function getAreaTypeOrder(areaType) {
    // Нормализуем тип площади для сравнения
    let normalized = areaType.trim();
    
    // Ищем точное совпадение (с учетом регистра)
    for (let i = 0; i < AREA_TYPE_ORDER.length; i++) {
        if (AREA_TYPE_ORDER[i] === normalized) {
            return i;
        }
    }
    
    // Если не найдено точное совпадение, проверяем без учета регистра
    const normalizedUpper = normalized.toUpperCase();
    for (let i = 0; i < AREA_TYPE_ORDER.length; i++) {
        if (AREA_TYPE_ORDER[i].toUpperCase() === normalizedUpper) {
            return i;
        }
    }
    
    // Если не найдено, проверяем частичное совпадение
    // Сначала проверяем более длинные варианты
    for (let i = AREA_TYPE_ORDER.length - 1; i >= 0; i--) {
        const orderType = AREA_TYPE_ORDER[i].toUpperCase();
        // Убираем скобки и лишние символы для сравнения
        const orderTypeClean = orderType.replace(/[()]/g, '').replace(/\s+/g, '').trim();
        const normalizedClean = normalizedUpper.replace(/[()]/g, '').replace(/\s+/g, '').trim();
        
        // Проверяем, содержит ли нормализованное значение ключевые слова из порядка
        if (normalizedClean.includes(orderTypeClean) || orderTypeClean.includes(normalizedClean)) {
            return i;
        }
    }
    
    // Если не найдено, возвращаем большое число для сортировки в конец
    return 999;
}

// Отображение списка групп в виде сводной таблицы
function displayGroups(groups, groupingMode = 'object') {
    const groupsList = document.getElementById('groupsList');
    const groupsSection = document.getElementById('groupsSection');
    
    groupsList.innerHTML = '';
    
    if (groupingMode === 'visualization') {
        if (boxplotsData) {
            displayBoxplotsInVisualization(boxplotsData);
        } else {
            groupsList.innerHTML = '<p>Данные для визуализации отсутствуют</p>';
        }
        return;
    } else if (groupingMode === 'characteristics') {
        if (characteristicsData && characteristicsData.length > 0) {
            displayCharacteristics(characteristicsData);
        } else {
            groupsList.innerHTML = '<p>Сводная информация не найдена</p>';
        }
        groupsSection.style.display = 'block';
        return;
    }
    
    if (groups.length === 0) {
        groupsList.innerHTML = '<p>Группы не найдены</p>';
        return;
    }
    
    if (groupingMode === 'type') {
        displayGroupsByType(groups);
    } else {
        displayGroupsByObject(groups);
    }
    
    groupsSection.style.display = 'block';
}

// Группировка по объектам (ЖК) - текущая логика
function displayGroupsByObject(groups) {
    const groupsList = document.getElementById('groupsList');
    
    // Группируем по названию объекта (source) и сохраняем информацию о том, основной ли это ЖК
    const objectsMap = new Map(); // название объекта -> {groups: [], isMain: boolean}
    
    groups.forEach(group => {
        // Используем source как название объекта
        const objectName = group.source || 'Неизвестный объект';
        
        if (!objectsMap.has(objectName)) {
            objectsMap.set(objectName, {
                groups: [],
                isMain: group.is_main || false  // Сохраняем флаг, является ли это основным ЖК
            });
        }
        objectsMap.get(objectName).groups.push(group);
    });
    
    // Создаем одну общую таблицу для всех объектов
    const table = document.createElement('table');
    table.className = 'groups-table';
    
    // Общий заголовок таблицы
    const thead = document.createElement('thead');
    
    // Первая строка заголовков
    const headerRow1 = document.createElement('tr');
    headerRow1.innerHTML = '<th rowspan="2"></th><th rowspan="2"></th><th rowspan="2">Количество</th><th rowspan="2">%</th><th rowspan="2">Общая<br>площадь,<br>м кв</th><th colspan="2">Минимум</th><th colspan="2">Среднее</th><th colspan="2">Максимум</th><th colspan="3">Цена,<br>кв м</th>';
    thead.appendChild(headerRow1);
    
    // Вторая строка заголовков (подколонки)
    const headerRow2 = document.createElement('tr');
    headerRow2.innerHTML = '<th>Площадь,<br>м кв</th><th>Стоимость,<br>млн руб</th><th>Площадь,<br>м кв</th><th>Стоимость,<br>млн руб</th><th>Площадь,<br>м кв</th><th>Стоимость,<br>млн руб</th><th>Мин</th><th>Сред</th><th>Макс</th>';
    thead.appendChild(headerRow2);
    
    table.appendChild(thead);
    
    // Тело таблицы
    const tbody = document.createElement('tbody');
    
    // Создаем строки для каждого объекта
    objectsMap.forEach((objectData, objectName) => {
        const objectGroups = objectData.groups;
        const isMain = objectData.isMain;
        
        // Собираем уникальные типы площади
        const areaTypes = new Set();
        objectGroups.forEach(group => {
            areaTypes.add(group.тип_площади);
        });
        
        // Сортируем типы площади по заданному порядку
        const sortedAreaTypes = Array.from(areaTypes).sort((a, b) => {
            const orderA = getAreaTypeOrder(a);
            const orderB = getAreaTypeOrder(b);
            if (orderA !== orderB) {
                return orderA - orderB;
            }
            // Если порядок одинаковый, сортируем по алфавиту
            return a.localeCompare(b);
        });
        
        // Создаем карту: тип площади -> количество, общая площадь, минимальные, средние, максимальные значения
        const areaTypeCounts = new Map();
        const areaTypeTotalAreas = new Map();
        const areaTypeMinCosts = new Map();
        const areaTypeMinAreas = new Map();
        const areaTypeMaxCosts = new Map();
        const areaTypeMaxAreas = new Map();
        const areaTypeAvgCosts = new Map();
        const areaTypeAvgAreas = new Map();
        
        // Для цен за м²
        const areaTypeMinPricePerSqm = new Map();
        const areaTypeAvgPricePerSqm = new Map();
        const areaTypeMaxPricePerSqm = new Map();
        const areaTypeAllPricePerSqm = new Map();
        
        // Для расчета средних значений нужно собрать все значения
        const areaTypeAllCosts = new Map();
        const areaTypeAllAreas = new Map();
        
        let totalCount = 0;
        let totalAreaSum = 0;
        let globalMinCost = Infinity;
        let globalMinArea = Infinity;
        let globalMaxCost = 0;
        let globalMaxArea = 0;
        const allCosts = [];
        
        objectGroups.forEach(group => {
            const areaType = group.тип_площади;
            const count = group.количество || 0;
            const totalArea = group.общая_площадь || 0;
            const minCost = group.мин_стоимость || 0;
            const minArea = group.мин_площадь || 0;
            const maxCost = group.макс_стоимость || 0;
            const maxArea = group.макс_площадь || 0;
            const avgCost = group.сред_стоимость || 0;
            const avgArea = group.сред_площадь || 0;
            const minPricePerSqm = group.мин_цена_за_м2 || 0;
            const avgPricePerSqm = group.сред_цена_за_м2 || 0;
            const maxPricePerSqm = group.макс_цена_за_м2 || 0;
            
            areaTypeCounts.set(areaType, (areaTypeCounts.get(areaType) || 0) + count);
            areaTypeTotalAreas.set(areaType, (areaTypeTotalAreas.get(areaType) || 0) + totalArea);
            
            // Для минимальных значений берем минимум среди всех групп этого типа
            if (!areaTypeMinCosts.has(areaType) || (minCost > 0 && minCost < areaTypeMinCosts.get(areaType))) {
                areaTypeMinCosts.set(areaType, minCost);
            }
            if (!areaTypeMinAreas.has(areaType) || (minArea > 0 && minArea < areaTypeMinAreas.get(areaType))) {
                areaTypeMinAreas.set(areaType, minArea);
            }
            
            // Для максимальных значений берем максимум среди всех групп этого типа
            if (!areaTypeMaxCosts.has(areaType) || maxCost > areaTypeMaxCosts.get(areaType)) {
                areaTypeMaxCosts.set(areaType, maxCost);
            }
            if (!areaTypeMaxAreas.has(areaType) || maxArea > areaTypeMaxAreas.get(areaType)) {
                areaTypeMaxAreas.set(areaType, maxArea);
            }
            
            // Для цен за м²
            if (!areaTypeMinPricePerSqm.has(areaType) || (minPricePerSqm > 0 && minPricePerSqm < areaTypeMinPricePerSqm.get(areaType))) {
                areaTypeMinPricePerSqm.set(areaType, minPricePerSqm);
            }
            if (!areaTypeMaxPricePerSqm.has(areaType) || maxPricePerSqm > areaTypeMaxPricePerSqm.get(areaType)) {
                areaTypeMaxPricePerSqm.set(areaType, maxPricePerSqm);
            }
            
            // Для средних значений собираем все значения для пересчета
            if (!areaTypeAllCosts.has(areaType)) {
                areaTypeAllCosts.set(areaType, []);
                areaTypeAllAreas.set(areaType, []);
                areaTypeAllPricePerSqm.set(areaType, []);
            }
            // Добавляем стоимости и площади из costs и areas групп
            if (group.costs && group.costs.length > 0) {
                areaTypeAllCosts.get(areaType).push(...group.costs);
            }
            // Добавляем площади из массива areas
            if (group.areas && group.areas.length > 0) {
                areaTypeAllAreas.get(areaType).push(...group.areas);
            }
            // Добавляем цены за м²
            if (group.price_per_sqm && group.price_per_sqm.length > 0) {
                areaTypeAllPricePerSqm.get(areaType).push(...group.price_per_sqm);
            }
            
            totalCount += count;
            totalAreaSum += totalArea;
            
            // Глобальные значения для строки ВСЕГО
            if (minCost > 0 && minCost < globalMinCost) {
                globalMinCost = minCost;
            }
            if (minArea > 0 && minArea < globalMinArea) {
                globalMinArea = minArea;
            }
            if (maxCost > globalMaxCost) {
                globalMaxCost = maxCost;
            }
            if (maxArea > globalMaxArea) {
                globalMaxArea = maxArea;
            }
            if (group.costs && group.costs.length > 0) {
                allCosts.push(...group.costs);
            }
        });
        
        // Пересчитываем средние значения для каждого типа площади
        areaTypeAllCosts.forEach((costs, areaType) => {
            if (costs.length > 0) {
                const avg = costs.reduce((a, b) => a + b, 0) / costs.length;
                areaTypeAvgCosts.set(areaType, avg);
            }
        });
        
        areaTypeAllAreas.forEach((areas, areaType) => {
            if (areas.length > 0) {
                const avg = areas.reduce((a, b) => a + b, 0) / areas.length;
                areaTypeAvgAreas.set(areaType, avg);
            }
        });
        
        // Пересчитываем средние цены за м²
        areaTypeAllPricePerSqm.forEach((prices, areaType) => {
            if (prices.length > 0) {
                const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
                areaTypeAvgPricePerSqm.set(areaType, avg);
            }
        });
        
        // Собираем все площади и цены за м² для расчета глобального среднего
        const allAreasForTotal = [];
        const allPricePerSqmForTotal = [];
        objectGroups.forEach(group => {
            if (group.areas && group.areas.length > 0) {
                allAreasForTotal.push(...group.areas);
            }
            if (group.price_per_sqm && group.price_per_sqm.length > 0) {
                allPricePerSqmForTotal.push(...group.price_per_sqm);
            }
        });
        
        // Глобальные средние для строки ВСЕГО
        // Используем среднее по группам (взвешенное по количеству), а не просто среднее всех стоимостей
        let globalAvgCost = 0;
        if (objectGroups.length > 0) {
            let totalWeightedCost = 0;
            let totalWeight = 0;
            objectGroups.forEach(group => {
                const count = group.количество || 0;
                const avgCost = group.сред_стоимость || 0;
                if (count > 0 && avgCost > 0) {
                    totalWeightedCost += avgCost * count;
                    totalWeight += count;
                }
            });
            if (totalWeight > 0) {
                globalAvgCost = totalWeightedCost / totalWeight;
            }
        }
        
        // Если не получилось рассчитать взвешенное среднее, используем простое среднее
        if (globalAvgCost === 0 && allCosts.length > 0) {
            globalAvgCost = allCosts.reduce((a, b) => a + b, 0) / allCosts.length;
        }
        
        const globalAvgArea = allAreasForTotal.length > 0 ? allAreasForTotal.reduce((a, b) => a + b, 0) / allAreasForTotal.length : 0;
        
        // Глобальные цены за м² для строки ВСЕГО
        let globalMinPricePerSqm = Infinity;
        let globalMaxPricePerSqm = 0;
        objectGroups.forEach(group => {
            const minPrice = group.мин_цена_за_м2 || 0;
            const maxPrice = group.макс_цена_за_м2 || 0;
            if (minPrice > 0 && minPrice < globalMinPricePerSqm) {
                globalMinPricePerSqm = minPrice;
            }
            if (maxPrice > globalMaxPricePerSqm) {
                globalMaxPricePerSqm = maxPrice;
            }
        });
        if (globalMinPricePerSqm === Infinity) globalMinPricePerSqm = 0;
        const globalAvgPricePerSqm = allPricePerSqmForTotal.length > 0 ? allPricePerSqmForTotal.reduce((a, b) => a + b, 0) / allPricePerSqmForTotal.length : 0;
        
        // Если не нашли минимумы, устанавливаем 0
        if (globalMinCost === Infinity) globalMinCost = 0;
        if (globalMinArea === Infinity) globalMinArea = 0;
        
        // Строка "ВСЕГО"
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row';
        if (isMain) {
            totalRow.classList.add('main-object-row');
        }
        
        // Название объекта слева (объединяет все строки для этого объекта)
        const objectNameCell = document.createElement('td');
        objectNameCell.textContent = objectName;
        objectNameCell.className = 'object-name-cell';
        if (isMain) {
            objectNameCell.classList.add('main-object-cell');
        }
        objectNameCell.rowSpan = sortedAreaTypes.length + 1; // +1 для строки ВСЕГО
        objectNameCell.style.verticalAlign = 'top';
        objectNameCell.style.paddingTop = '10px';
        totalRow.appendChild(objectNameCell);
        
        const totalLabelCell = document.createElement('td');
        totalLabelCell.textContent = 'ВСЕГО';
        totalLabelCell.className = 'group-name total-label';
        totalRow.appendChild(totalLabelCell);
        
        const totalCountCell = document.createElement('td');
        totalCountCell.textContent = totalCount;
        totalCountCell.className = 'has-data';
        totalRow.appendChild(totalCountCell);
        
        const totalPercentCell = document.createElement('td');
        totalPercentCell.textContent = '100%';
        totalPercentCell.className = 'has-data';
        totalRow.appendChild(totalPercentCell);
        
        const totalAreaCell = document.createElement('td');
        totalAreaCell.textContent = totalAreaSum.toFixed(2);
        totalAreaCell.className = 'has-data';
        totalRow.appendChild(totalAreaCell);
        
        // Минимальная площадь для ВСЕГО
        const totalMinAreaCell = document.createElement('td');
        totalMinAreaCell.textContent = globalMinArea > 0 ? globalMinArea.toFixed(2) : '-';
        totalMinAreaCell.className = 'has-data';
        totalRow.appendChild(totalMinAreaCell);
        
        // Минимальная стоимость для ВСЕГО
        const totalMinCostCell = document.createElement('td');
        totalMinCostCell.textContent = globalMinCost > 0 ? (globalMinCost / 1000000).toFixed(2) : '-';
        totalMinCostCell.className = 'has-data';
        totalRow.appendChild(totalMinCostCell);
        
        // Средняя площадь для ВСЕГО
        const totalAvgAreaCell = document.createElement('td');
        totalAvgAreaCell.textContent = globalAvgArea > 0 ? globalAvgArea.toFixed(2) : '-';
        totalAvgAreaCell.className = 'has-data';
        totalRow.appendChild(totalAvgAreaCell);
        
        // Средняя стоимость для ВСЕГО
        const totalAvgCostCell = document.createElement('td');
        totalAvgCostCell.textContent = globalAvgCost > 0 ? (globalAvgCost / 1000000).toFixed(2) : '-';
        totalAvgCostCell.className = 'has-data';
        totalRow.appendChild(totalAvgCostCell);
        
        // Максимальная площадь для ВСЕГО
        const totalMaxAreaCell = document.createElement('td');
        totalMaxAreaCell.textContent = globalMaxArea > 0 ? globalMaxArea.toFixed(2) : '-';
        totalMaxAreaCell.className = 'has-data';
        totalRow.appendChild(totalMaxAreaCell);
        
        // Максимальная стоимость для ВСЕГО
        const totalMaxCostCell = document.createElement('td');
        totalMaxCostCell.textContent = globalMaxCost > 0 ? (globalMaxCost / 1000000).toFixed(2) : '-';
        totalMaxCostCell.className = 'has-data';
        totalRow.appendChild(totalMaxCostCell);
        
        // Минимальная цена за м² для ВСЕГО
        const totalMinPricePerSqmCell = document.createElement('td');
        totalMinPricePerSqmCell.textContent = globalMinPricePerSqm > 0 ? Math.round(globalMinPricePerSqm).toLocaleString('ru-RU') : '-';
        totalMinPricePerSqmCell.className = 'has-data';
        totalRow.appendChild(totalMinPricePerSqmCell);
        
        // Средняя цена за м² для ВСЕГО
        const totalAvgPricePerSqmCell = document.createElement('td');
        totalAvgPricePerSqmCell.textContent = globalAvgPricePerSqm > 0 ? Math.round(globalAvgPricePerSqm).toLocaleString('ru-RU') : '-';
        totalAvgPricePerSqmCell.className = 'has-data';
        totalRow.appendChild(totalAvgPricePerSqmCell);
        
        // Максимальная цена за м² для ВСЕГО
        const totalMaxPricePerSqmCell = document.createElement('td');
        totalMaxPricePerSqmCell.textContent = globalMaxPricePerSqm > 0 ? Math.round(globalMaxPricePerSqm).toLocaleString('ru-RU') : '-';
        totalMaxPricePerSqmCell.className = 'has-data';
        totalRow.appendChild(totalMaxPricePerSqmCell);
        
        tbody.appendChild(totalRow);
        
        // Строки для каждого типа площади
        sortedAreaTypes.forEach((areaType, index) => {
            const row = document.createElement('tr');
            if (isMain) {
                row.classList.add('main-object-row');
            }
            
            // Название типа площади (название объекта уже в первой строке)
            const nameCell = document.createElement('td');
            nameCell.textContent = areaType;
            nameCell.className = 'group-name';
            row.appendChild(nameCell);
            
            // Количество
            const countCell = document.createElement('td');
            const count = areaTypeCounts.get(areaType) || 0;
            countCell.textContent = count;
            countCell.className = count > 0 ? 'has-data' : 'no-data';
            row.appendChild(countCell);
            
            // Процент
            const percentCell = document.createElement('td');
            const percent = totalCount > 0 ? Math.round((count / totalCount) * 100) : 0;
            percentCell.textContent = percent + '%';
            percentCell.className = count > 0 ? 'has-data' : 'no-data';
            row.appendChild(percentCell);
            
            // Общая площадь
            const areaCell = document.createElement('td');
            const totalArea = areaTypeTotalAreas.get(areaType) || 0;
            areaCell.textContent = totalArea.toFixed(2);
            areaCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && totalArea > 0) {
                areaCell.dataset.columnIndex = '2'; // Общая площадь
                areaCell.dataset.value = totalArea;
            }
            row.appendChild(areaCell);
            
            // Минимальная площадь
            const minAreaCell = document.createElement('td');
            const minArea = areaTypeMinAreas.get(areaType) || 0;
            minAreaCell.textContent = minArea > 0 ? minArea.toFixed(2) : '-';
            minAreaCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && minArea > 0) {
                minAreaCell.dataset.columnIndex = '3'; // Мин площадь
                minAreaCell.dataset.value = minArea;
            }
            row.appendChild(minAreaCell);
            
            // Минимальная стоимость
            const minCostCell = document.createElement('td');
            const minCost = areaTypeMinCosts.get(areaType) || 0;
            minCostCell.textContent = minCost > 0 ? (minCost / 1000000).toFixed(2) : '-';
            minCostCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && minCost > 0) {
                minCostCell.dataset.columnIndex = '4'; // Мин стоимость
                minCostCell.dataset.value = minCost;
            }
            row.appendChild(minCostCell);
            
            // Средняя площадь
            const avgAreaCell = document.createElement('td');
            const avgArea = areaTypeAvgAreas.get(areaType) || 0;
            avgAreaCell.textContent = avgArea > 0 ? avgArea.toFixed(2) : '-';
            avgAreaCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && avgArea > 0) {
                avgAreaCell.dataset.columnIndex = '5'; // Сред площадь
                avgAreaCell.dataset.value = avgArea;
            }
            row.appendChild(avgAreaCell);
            
            // Средняя стоимость
            const avgCostCell = document.createElement('td');
            const avgCost = areaTypeAvgCosts.get(areaType) || 0;
            avgCostCell.textContent = avgCost > 0 ? (avgCost / 1000000).toFixed(2) : '-';
            avgCostCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && avgCost > 0) {
                avgCostCell.dataset.columnIndex = '6'; // Сред стоимость
                avgCostCell.dataset.value = avgCost;
            }
            row.appendChild(avgCostCell);
            
            // Максимальная площадь
            const maxAreaCell = document.createElement('td');
            const maxArea = areaTypeMaxAreas.get(areaType) || 0;
            maxAreaCell.textContent = maxArea > 0 ? maxArea.toFixed(2) : '-';
            maxAreaCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && maxArea > 0) {
                maxAreaCell.dataset.columnIndex = '7'; // Макс площадь
                maxAreaCell.dataset.value = maxArea;
            }
            row.appendChild(maxAreaCell);
            
            // Максимальная стоимость
            const maxCostCell = document.createElement('td');
            const maxCost = areaTypeMaxCosts.get(areaType) || 0;
            maxCostCell.textContent = maxCost > 0 ? (maxCost / 1000000).toFixed(2) : '-';
            maxCostCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && maxCost > 0) {
                maxCostCell.dataset.columnIndex = '8'; // Макс стоимость
                maxCostCell.dataset.value = maxCost;
            }
            row.appendChild(maxCostCell);
            
            // Минимальная цена за м²
            const minPricePerSqmCell = document.createElement('td');
            const minPricePerSqm = areaTypeMinPricePerSqm.get(areaType) || 0;
            minPricePerSqmCell.textContent = minPricePerSqm > 0 ? Math.round(minPricePerSqm).toLocaleString('ru-RU') : '-';
            minPricePerSqmCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && minPricePerSqm > 0) {
                minPricePerSqmCell.dataset.columnIndex = '9'; // Мин цена за м²
                minPricePerSqmCell.dataset.value = minPricePerSqm;
            }
            row.appendChild(minPricePerSqmCell);
            
            // Средняя цена за м²
            const avgPricePerSqmCell = document.createElement('td');
            const avgPricePerSqm = areaTypeAvgPricePerSqm.get(areaType) || 0;
            avgPricePerSqmCell.textContent = avgPricePerSqm > 0 ? Math.round(avgPricePerSqm).toLocaleString('ru-RU') : '-';
            avgPricePerSqmCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && avgPricePerSqm > 0) {
                avgPricePerSqmCell.dataset.columnIndex = '10'; // Сред цена за м²
                avgPricePerSqmCell.dataset.value = avgPricePerSqm;
            }
            row.appendChild(avgPricePerSqmCell);
            
            // Максимальная цена за м²
            const maxPricePerSqmCell = document.createElement('td');
            const maxPricePerSqm = areaTypeMaxPricePerSqm.get(areaType) || 0;
            maxPricePerSqmCell.textContent = maxPricePerSqm > 0 ? Math.round(maxPricePerSqm).toLocaleString('ru-RU') : '-';
            maxPricePerSqmCell.className = count > 0 ? 'has-data' : 'no-data';
            if (count > 0 && maxPricePerSqm > 0) {
                maxPricePerSqmCell.dataset.columnIndex = '11'; // Макс цена за м²
                maxPricePerSqmCell.dataset.value = maxPricePerSqm;
            }
            row.appendChild(maxPricePerSqmCell);
            
            tbody.appendChild(row);
        });
    });
    
    table.appendChild(tbody);
    groupsList.appendChild(table);
}

// Группировка по типам площади - сначала типы, потом ЖК
function displayGroupsByType(groups) {
    const groupsList = document.getElementById('groupsList');
    
    // Сначала группируем по типам площади
    const areaTypeMap = new Map(); // тип площади -> {groups: []}
    
    groups.forEach(group => {
        const areaType = group.тип_площади || 'Неизвестный тип';
        if (!areaTypeMap.has(areaType)) {
            areaTypeMap.set(areaType, []);
        }
        areaTypeMap.get(areaType).push(group);
    });
    
    // Сортируем типы площади по заданному порядку
    const sortedAreaTypes = Array.from(areaTypeMap.keys()).sort((a, b) => {
        const orderA = getAreaTypeOrder(a);
        const orderB = getAreaTypeOrder(b);
        if (orderA !== orderB) {
            return orderA - orderB;
        }
        return a.localeCompare(b);
    });
    
    // Создаем одну общую таблицу
    const table = document.createElement('table');
    table.className = 'groups-table';
    
    // Общий заголовок таблицы
    const thead = document.createElement('thead');
    
    // Первая строка заголовков
    const headerRow1 = document.createElement('tr');
    headerRow1.innerHTML = '<th rowspan="2"></th><th rowspan="2"></th><th rowspan="2">Количество</th><th rowspan="2">%</th><th rowspan="2">Общая площадь, м кв</th><th colspan="2">Минимум</th><th colspan="2">Среднее</th><th colspan="2">Максимум</th><th colspan="3">Цена, кв м</th>';
    thead.appendChild(headerRow1);
    
    // Вторая строка заголовков (подколонки)
    const headerRow2 = document.createElement('tr');
    headerRow2.innerHTML = '<th>Площадь, м кв</th><th>Стоимость, млн руб</th><th>Площадь, м кв</th><th>Стоимость, млн руб</th><th>Площадь, м кв</th><th>Стоимость, млн руб</th><th>Мин</th><th>Сред</th><th>Макс</th>';
    thead.appendChild(headerRow2);
    
    table.appendChild(thead);
    
    // Тело таблицы
    const tbody = document.createElement('tbody');
    
    // Для каждого типа площади
    sortedAreaTypes.forEach(areaType => {
        const typeGroups = areaTypeMap.get(areaType);
        
        // Группируем по объектам для этого типа
        const objectsMap = new Map(); // название объекта -> {groups: [], isMain: boolean}
        
        typeGroups.forEach(group => {
            const objectName = group.source || 'Неизвестный объект';
            if (!objectsMap.has(objectName)) {
                objectsMap.set(objectName, {
                    groups: [],
                    isMain: group.is_main || false
                });
            }
            objectsMap.get(objectName).groups.push(group);
        });
        
        // Сортируем объекты: сначала основные, потом конкуренты, внутри каждой группы - по средней стоимости за м²
        const sortedObjects = Array.from(objectsMap.entries()).sort((a, b) => {
            // Сначала основные, потом конкуренты
            if (a[1].isMain !== b[1].isMain) {
                return b[1].isMain ? 1 : -1; // Основные первыми
            }
            
            // Внутри каждой группы сортируем по средней стоимости за м² (от меньшего к большему)
            const pricesA = [];
            const pricesB = [];
            
            // Собираем все цены за м² для объекта A
            a[1].groups.forEach(group => {
                if (group.price_per_sqm && group.price_per_sqm.length > 0) {
                    pricesA.push(...group.price_per_sqm);
                } else if (group.сред_цена_за_м2 && group.сред_цена_за_м2 > 0) {
                    pricesA.push(group.сред_цена_за_м2);
                }
            });
            
            // Собираем все цены за м² для объекта B
            b[1].groups.forEach(group => {
                if (group.price_per_sqm && group.price_per_sqm.length > 0) {
                    pricesB.push(...group.price_per_sqm);
                } else if (group.сред_цена_за_м2 && group.сред_цена_за_м2 > 0) {
                    pricesB.push(group.сред_цена_за_м2);
                }
            });
            
            // Вычисляем среднюю стоимость за м²
            const avgPriceA = pricesA.length > 0 ? pricesA.reduce((sum, p) => sum + p, 0) / pricesA.length : 0;
            const avgPriceB = pricesB.length > 0 ? pricesB.reduce((sum, p) => sum + p, 0) / pricesB.length : 0;
            
            // Сортируем по средней стоимости за м² (от меньшего к большему)
            if (avgPriceA !== avgPriceB) {
                return avgPriceA - avgPriceB;
            }
            
            // Если стоимости равны, сортируем по названию
            return a[0].localeCompare(b[0]);
        });
        
        // Собираем статистику для типа площади
        let typeTotalCount = 0;
        let typeTotalArea = 0;
        const typeAllCosts = [];
        const typeAllAreas = [];
        const typeAllPricePerSqm = [];
        let typeMinCost = Infinity;
        let typeMinArea = Infinity;
        let typeMaxCost = 0;
        let typeMaxArea = 0;
        let typeMinPricePerSqm = Infinity;
        let typeMaxPricePerSqm = 0;
        
        sortedObjects.forEach(([objectName, objectData]) => {
            objectData.groups.forEach(group => {
                const count = group.количество || 0;
                const totalArea = group.общая_площадь || 0;
                const minCost = group.мин_стоимость || 0;
                const minArea = group.мин_площадь || 0;
                const maxCost = group.макс_стоимость || 0;
                const maxArea = group.макс_площадь || 0;
                const minPricePerSqm = group.мин_цена_за_м2 || 0;
                const maxPricePerSqm = group.макс_цена_за_м2 || 0;
                
                typeTotalCount += count;
                typeTotalArea += totalArea;
                
                if (group.costs && group.costs.length > 0) {
                    typeAllCosts.push(...group.costs);
                }
                if (group.areas && group.areas.length > 0) {
                    typeAllAreas.push(...group.areas);
                }
                if (group.price_per_sqm && group.price_per_sqm.length > 0) {
                    typeAllPricePerSqm.push(...group.price_per_sqm);
                }
                
                if (minCost > 0 && minCost < typeMinCost) typeMinCost = minCost;
                if (minArea > 0 && minArea < typeMinArea) typeMinArea = minArea;
                if (maxCost > typeMaxCost) typeMaxCost = maxCost;
                if (maxArea > typeMaxArea) typeMaxArea = maxArea;
                if (minPricePerSqm > 0 && minPricePerSqm < typeMinPricePerSqm) typeMinPricePerSqm = minPricePerSqm;
                if (maxPricePerSqm > typeMaxPricePerSqm) typeMaxPricePerSqm = maxPricePerSqm;
            });
        });
        
        if (typeMinCost === Infinity) typeMinCost = 0;
        if (typeMinArea === Infinity) typeMinArea = 0;
        if (typeMinPricePerSqm === Infinity) typeMinPricePerSqm = 0;
        
        const typeAvgCost = typeAllCosts.length > 0 ? typeAllCosts.reduce((a, b) => a + b, 0) / typeAllCosts.length : 0;
        const typeAvgArea = typeAllAreas.length > 0 ? typeAllAreas.reduce((a, b) => a + b, 0) / typeAllAreas.length : 0;
        const typeAvgPricePerSqm = typeAllPricePerSqm.length > 0 ? typeAllPricePerSqm.reduce((a, b) => a + b, 0) / typeAllPricePerSqm.length : 0;
        
        // Создаем строки для каждого объекта этого типа
        sortedObjects.forEach(([objectName, objectData], objIndex) => {
            const objectGroups = objectData.groups;
            const isMain = objectData.isMain;
            
            // Собираем статистику для объекта
            let objTotalCount = 0;
            let objTotalArea = 0;
            let objMinCost = Infinity;
            let objMinArea = Infinity;
            let objMaxCost = 0;
            let objMaxArea = 0;
            const objAllCosts = [];
            const objAllAreas = [];
            const objAllPricePerSqm = [];
            let objMinPricePerSqm = Infinity;
            let objMaxPricePerSqm = 0;
            
            objectGroups.forEach(group => {
                const count = group.количество || 0;
                const totalArea = group.общая_площадь || 0;
                const minCost = group.мин_стоимость || 0;
                const minArea = group.мин_площадь || 0;
                const maxCost = group.макс_стоимость || 0;
                const maxArea = group.макс_площадь || 0;
                const minPricePerSqm = group.мин_цена_за_м2 || 0;
                const maxPricePerSqm = group.макс_цена_за_м2 || 0;
                
                objTotalCount += count;
                objTotalArea += totalArea;
                
                if (group.costs && group.costs.length > 0) {
                    objAllCosts.push(...group.costs);
                }
                if (group.areas && group.areas.length > 0) {
                    objAllAreas.push(...group.areas);
                }
                if (group.price_per_sqm && group.price_per_sqm.length > 0) {
                    objAllPricePerSqm.push(...group.price_per_sqm);
                }
                
                if (minCost > 0 && minCost < objMinCost) objMinCost = minCost;
                if (minArea > 0 && minArea < objMinArea) objMinArea = minArea;
                if (maxCost > objMaxCost) objMaxCost = maxCost;
                if (maxArea > objMaxArea) objMaxArea = maxArea;
                if (minPricePerSqm > 0 && minPricePerSqm < objMinPricePerSqm) objMinPricePerSqm = minPricePerSqm;
                if (maxPricePerSqm > objMaxPricePerSqm) objMaxPricePerSqm = maxPricePerSqm;
            });
            
            if (objMinCost === Infinity) objMinCost = 0;
            if (objMinArea === Infinity) objMinArea = 0;
            if (objMinPricePerSqm === Infinity) objMinPricePerSqm = 0;
            
            const objAvgCost = objAllCosts.length > 0 ? objAllCosts.reduce((a, b) => a + b, 0) / objAllCosts.length : 0;
            const objAvgArea = objAllAreas.length > 0 ? objAllAreas.reduce((a, b) => a + b, 0) / objAllAreas.length : 0;
            const objAvgPricePerSqm = objAllPricePerSqm.length > 0 ? objAllPricePerSqm.reduce((a, b) => a + b, 0) / objAllPricePerSqm.length : 0;
            
            const row = document.createElement('tr');
            row.dataset.areaType = areaType; // Помечаем строку типом площади для группировки
            if (isMain) {
                row.classList.add('main-object-row');
            }
            
            // Название типа площади (только в первой строке для этого типа)
            if (objIndex === 0) {
                const typeNameCell = document.createElement('td');
                typeNameCell.textContent = areaType;
                typeNameCell.className = 'object-name-cell';
                typeNameCell.rowSpan = sortedObjects.length + 1; // +1 для строки ВСЕГО
                typeNameCell.style.verticalAlign = 'top';
                typeNameCell.style.paddingTop = '10px';
                row.appendChild(typeNameCell);
            }
            
            // Название объекта
            const objectNameCell = document.createElement('td');
            objectNameCell.textContent = objectName;
            objectNameCell.className = 'group-name';
            if (isMain) {
                objectNameCell.classList.add('main-object-cell');
            }
            // Определяем left позицию для второго столбца (нужно учесть ширину первого)
            row.appendChild(objectNameCell);
            
            // Заполняем остальные ячейки
            addDataCells(row, objTotalCount, typeTotalCount, objTotalArea, objMinArea, objMinCost, objAvgArea, objAvgCost, objMaxArea, objMaxCost, objMinPricePerSqm, objAvgPricePerSqm, objMaxPricePerSqm, objTotalCount > 0, false);
            
            tbody.appendChild(row);
        });
        
        // Строка "ВСЕГО" для типа площади (всегда создаем, даже если нет объектов)
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row total-row-by-type';
        totalRow.dataset.areaType = areaType; // Помечаем строку типом площади
        totalRow.dataset.isTotal = 'true'; // Помечаем как строку "ВСЕГО"
        
        // Если нет объектов, все равно нужно добавить пустую ячейку для типа площади
        if (sortedObjects.length === 0) {
            const typeNameCell = document.createElement('td');
            typeNameCell.textContent = areaType;
            typeNameCell.className = 'object-name-cell';
            typeNameCell.rowSpan = 2; // +1 для строки ВСЕГО
            typeNameCell.style.verticalAlign = 'top';
            typeNameCell.style.paddingTop = '10px';
            totalRow.appendChild(typeNameCell);
        }
        
        const totalLabelCell = document.createElement('td');
        totalLabelCell.textContent = 'ВСЕГО';
        totalLabelCell.className = 'group-name total-label';
        totalLabelCell.style.paddingLeft = '20px'; // Отступ для визуального выделения
        totalRow.appendChild(totalLabelCell);
        
        addDataCells(totalRow, typeTotalCount, typeTotalCount, typeTotalArea, typeMinArea, typeMinCost, typeAvgArea, typeAvgCost, typeMaxArea, typeMaxCost, typeMinPricePerSqm, typeAvgPricePerSqm, typeMaxPricePerSqm, typeTotalCount > 0, true);
        
        tbody.appendChild(totalRow);
    });
    
    table.appendChild(tbody);
    groupsList.appendChild(table);
    
    // Применяем цветовое кодирование для столбцов (только для режима "По типам")
    applyColorCoding(table);
}

// Вспомогательная функция для добавления ячеек с данными
function addDataCells(row, count, totalCount, totalArea, minArea, minCost, avgArea, avgCost, maxArea, maxCost, minPricePerSqm, avgPricePerSqm, maxPricePerSqm, hasData, isTotalRow = false) {
    const percent = totalCount > 0 ? Math.round((count / totalCount) * 100) : 0;
    
    const countCell = document.createElement('td');
    countCell.textContent = count;
    countCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) countCell.dataset.isTotal = 'true';
    if (!isTotalRow) countCell.dataset.columnIndex = '0'; // Количество
    row.appendChild(countCell);
    
    const percentCell = document.createElement('td');
    percentCell.textContent = percent + '%';
    percentCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) percentCell.dataset.isTotal = 'true';
    if (!isTotalRow) percentCell.dataset.columnIndex = '1'; // %
    row.appendChild(percentCell);
    
    const areaCell = document.createElement('td');
    areaCell.textContent = totalArea.toFixed(2);
    areaCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) areaCell.dataset.isTotal = 'true';
    if (!isTotalRow) {
        areaCell.dataset.columnIndex = '2'; // Общая площадь
        areaCell.dataset.value = totalArea;
    }
    row.appendChild(areaCell);
    
    const minAreaCell = document.createElement('td');
    minAreaCell.textContent = minArea > 0 ? minArea.toFixed(2) : '-';
    minAreaCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) minAreaCell.dataset.isTotal = 'true';
    if (!isTotalRow && minArea > 0) {
        minAreaCell.dataset.columnIndex = '3'; // Мин площадь
        minAreaCell.dataset.value = minArea;
    }
    row.appendChild(minAreaCell);
    
    const minCostCell = document.createElement('td');
    minCostCell.textContent = minCost > 0 ? (minCost / 1000000).toFixed(2) : '-';
    minCostCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) minCostCell.dataset.isTotal = 'true';
    if (!isTotalRow && minCost > 0) {
        minCostCell.dataset.columnIndex = '4'; // Мин стоимость
        minCostCell.dataset.value = minCost;
    }
    row.appendChild(minCostCell);
    
    const avgAreaCell = document.createElement('td');
    avgAreaCell.textContent = avgArea > 0 ? avgArea.toFixed(2) : '-';
    avgAreaCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) avgAreaCell.dataset.isTotal = 'true';
    if (!isTotalRow && avgArea > 0) {
        avgAreaCell.dataset.columnIndex = '5'; // Сред площадь
        avgAreaCell.dataset.value = avgArea;
    }
    row.appendChild(avgAreaCell);
    
    const avgCostCell = document.createElement('td');
    avgCostCell.textContent = avgCost > 0 ? (avgCost / 1000000).toFixed(2) : '-';
    avgCostCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) avgCostCell.dataset.isTotal = 'true';
    if (!isTotalRow && avgCost > 0) {
        avgCostCell.dataset.columnIndex = '6'; // Сред стоимость
        avgCostCell.dataset.value = avgCost;
    }
    row.appendChild(avgCostCell);
    
    const maxAreaCell = document.createElement('td');
    maxAreaCell.textContent = maxArea > 0 ? maxArea.toFixed(2) : '-';
    maxAreaCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) maxAreaCell.dataset.isTotal = 'true';
    if (!isTotalRow && maxArea > 0) {
        maxAreaCell.dataset.columnIndex = '7'; // Макс площадь
        maxAreaCell.dataset.value = maxArea;
    }
    row.appendChild(maxAreaCell);
    
    const maxCostCell = document.createElement('td');
    maxCostCell.textContent = maxCost > 0 ? (maxCost / 1000000).toFixed(2) : '-';
    maxCostCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) maxCostCell.dataset.isTotal = 'true';
    if (!isTotalRow && maxCost > 0) {
        maxCostCell.dataset.columnIndex = '8'; // Макс стоимость
        maxCostCell.dataset.value = maxCost;
    }
    row.appendChild(maxCostCell);
    
    const minPricePerSqmCell = document.createElement('td');
    minPricePerSqmCell.textContent = minPricePerSqm > 0 ? Math.round(minPricePerSqm).toLocaleString('ru-RU') : '-';
    minPricePerSqmCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) minPricePerSqmCell.dataset.isTotal = 'true';
    if (!isTotalRow && minPricePerSqm > 0) {
        minPricePerSqmCell.dataset.columnIndex = '9'; // Мин цена за м²
        minPricePerSqmCell.dataset.value = minPricePerSqm;
    }
    row.appendChild(minPricePerSqmCell);
    
    const avgPricePerSqmCell = document.createElement('td');
    avgPricePerSqmCell.textContent = avgPricePerSqm > 0 ? Math.round(avgPricePerSqm).toLocaleString('ru-RU') : '-';
    avgPricePerSqmCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) avgPricePerSqmCell.dataset.isTotal = 'true';
    if (!isTotalRow && avgPricePerSqm > 0) {
        avgPricePerSqmCell.dataset.columnIndex = '10'; // Сред цена за м²
        avgPricePerSqmCell.dataset.value = avgPricePerSqm;
    }
    row.appendChild(avgPricePerSqmCell);
    
    const maxPricePerSqmCell = document.createElement('td');
    maxPricePerSqmCell.textContent = maxPricePerSqm > 0 ? Math.round(maxPricePerSqm).toLocaleString('ru-RU') : '-';
    maxPricePerSqmCell.className = hasData ? 'has-data' : 'no-data';
    if (isTotalRow) maxPricePerSqmCell.dataset.isTotal = 'true';
    if (!isTotalRow && maxPricePerSqm > 0) {
        maxPricePerSqmCell.dataset.columnIndex = '11'; // Макс цена за м²
        maxPricePerSqmCell.dataset.value = maxPricePerSqm;
    }
    row.appendChild(maxPricePerSqmCell);
}

// Применяет цветовое кодирование к столбцам таблицы (только для режима "По типам")
// Кодирование применяется отдельно для каждого типа площади
function applyColorCoding(table) {
    // Определяем индексы столбцов для кодирования (исключая Количество, %)
    // После Количество (индекс 2) идет % (индекс 1), затем Общая площадь (индекс 2)
    // Мин/Сред/Макс площадь и стоимость (индексы 3-8), цены за м² (индексы 9-11)
    const columnIndices = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]; // Общая площадь, Мин/Сред/Макс площадь и стоимость, цены за м²
    
    // Собираем все уникальные типы площади из строк таблицы
    const areaTypes = new Set();
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const areaType = row.dataset.areaType;
        if (areaType && !row.dataset.isTotal) { // Исключаем строки "ВСЕГО"
            areaTypes.add(areaType);
        }
    });
    
    // Для каждого типа площади отдельно применяем кодирование
    areaTypes.forEach(areaType => {
        // Для каждого столбца собираем значения только для этого типа площади
        columnIndices.forEach(columnIndex => {
            // Находим все ячейки этого столбца, которые принадлежат строкам данного типа площади
            const cells = [];
            rows.forEach(row => {
                if (row.dataset.areaType === areaType && !row.dataset.isTotal) {
                    const cellsInRow = row.querySelectorAll('td');
                    const cell = Array.from(cellsInRow).find(c => 
                        c.dataset.columnIndex === String(columnIndex)
                    );
                    if (cell) {
                        cells.push(cell);
                    }
                }
            });
            
            if (cells.length === 0) return;
            
            // Собираем все значения для этого столбца в рамках данного типа
            const values = [];
            cells.forEach(cell => {
                const value = parseFloat(cell.dataset.value);
                if (!isNaN(value) && value > 0) {
                    values.push(value);
                }
            });
            
            if (values.length === 0) return;
            
            // Находим минимум и максимум для этого типа площади
            const min = Math.min(...values);
            const max = Math.max(...values);
            const range = max - min;
            
            if (range === 0) return; // Все значения одинаковые
            
            // Применяем цветовое кодирование только к ячейкам этого типа
            cells.forEach(cell => {
                const value = parseFloat(cell.dataset.value);
                if (!isNaN(value) && value > 0) {
                    // Вычисляем интенсивность от 0 до 1 в рамках этого типа
                    const intensity = (value - min) / range;
                    // Применяем более спокойный градиент от светлого к более темному
                    const alpha = 0.15 + (intensity * 0.25); // От 0.15 до 0.4 (более спокойно)
                    cell.style.backgroundColor = `rgba(102, 126, 234, ${alpha})`;
                }
            });
        });
    });
}

// Отображает боксплоты в секции результатов
function displayBoxplotsInVisualization(boxplots) {
    const groupsList = document.getElementById('groupsList');
    
    if (!groupsList) {
        console.error('Элемент groupsList не найден');
        return;
    }
    
    groupsList.innerHTML = '';
    
    if (!boxplots || Object.keys(boxplots).length === 0) {
        groupsList.innerHTML = '<p>Данные для визуализации отсутствуют</p>';
        return;
    }

    // Проверяем наличие Plotly
    if (typeof Plotly === 'undefined') {
        console.error('Plotly не загружен');
        groupsList.innerHTML = '<p style="color: red;">Ошибка: Plotly не загружен. Проверьте подключение к интернету.</p>';
        return;
    }

    console.log('Отображаем интерактивные графики:', Object.keys(boxplots).length, 'штук');
    
    // Порядок типов площади для отображения
    const areaTypeOrder = [
        'XS (Студия)',
        '1к',
        'S (2Евро)',
        '2к',
        'M (3Евро)',
        '3к',
        'L (4Евро)',
        '4к',
        '5к',
        '6к',
        '7к',
        '8к'
    ];
    
    // Сортируем типы площади по порядку
    const sortedTypes = Object.keys(boxplots).sort((a, b) => {
        const indexA = areaTypeOrder.indexOf(a);
        const indexB = areaTypeOrder.indexOf(b);
        if (indexA === -1 && indexB === -1) return a.localeCompare(b);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
    });
    
    sortedTypes.forEach(areaType => {
        const boxplotData = boxplots[areaType];
        if (!boxplotData || !boxplotData.data || !boxplotData.layout) return;

        const boxplotDiv = document.createElement('div');
        boxplotDiv.className = 'chart-box';
        boxplotDiv.style.marginBottom = '30px';
        boxplotDiv.style.background = 'white';
        boxplotDiv.style.padding = '20px';
        boxplotDiv.style.borderRadius = '8px';
        boxplotDiv.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';

        const title = document.createElement('h4');
        title.textContent = boxplotData.title || `Цены за м², ${areaType}`;
        title.style.marginBottom = '15px';
        title.style.color = '#555';

        const plotContainer = document.createElement('div');
        plotContainer.id = boxplotData.div_id || `boxplot_${areaType}`;
        plotContainer.style.width = '100%';
        plotContainer.style.height = '500px';

        boxplotDiv.appendChild(title);
        boxplotDiv.appendChild(plotContainer);
        groupsList.appendChild(boxplotDiv);

        // Рисуем интерактивный график
        try {
            Plotly.newPlot(plotContainer.id, boxplotData.data, boxplotData.layout, {
                responsive: true,
                displayModeBar: true
            });
        } catch (error) {
            console.error('Ошибка при создании интерактивного графика для', areaType, error);
            plotContainer.innerHTML = '<p style="color: red;">Ошибка при отображении графика</p>';
        }
    });
}

// Отображение сводной таблицы "Сводная"
function displayCharacteristics(chars) {
    const groupsList = document.getElementById('groupsList');
    groupsList.innerHTML = '';

    if (!chars || chars.length === 0) {
        groupsList.innerHTML = '<p>Сводная информация не найдена</p>';
        return;
    }

    // Подготавливаем статистику по количеству квартир и средней стоимости (в т.ч. за м²) из groupsData
    // Структура: name -> {
    //   total: number,
    //   perSqm: number[],          // все цены за м² по ЖК (по всем типам)
    //   byType: { [areaType]: {    // статистика по каждому типу
    //     count: number,
    //     costs: number[],         // абсолютные стоимости
    //     perSqm: number[],        // цены за м²
    //     avgCost?: number         // средняя абсолютная стоимость по типу
    //   } }
    // }
    const statsByObject = new Map();
    if (Array.isArray(groupsData)) {
        groupsData.forEach(g => {
            const name = g.source || 'Неизвестный объект';
            const count = g.количество || 0;
            const areaType = g.тип_площади || 'Неизвестный тип';
            const costs = g.costs || [];
            const areas = g.areas || [];
            
            if (!statsByObject.has(name)) {
                statsByObject.set(name, { total: 0, perSqm: [], byType: {} });
            }
            const stat = statsByObject.get(name);
            stat.total += count;
            
            if (!stat.byType[areaType]) {
                stat.byType[areaType] = { count: 0, costs: [], perSqm: [] };
            }
            stat.byType[areaType].count += count;
            if (costs && costs.length > 0) {
                stat.byType[areaType].costs.push(...costs);
                // Считаем цену за м² для каждой квартиры в группе
                if (areas && areas.length === costs.length) {
                    for (let i = 0; i < costs.length; i++) {
                        const price = costs[i];
                        const area = areas[i];
                        if (area && area > 0) {
                            const pricePerSqm = price / area;
                            stat.byType[areaType].perSqm.push(pricePerSqm);
                            stat.perSqm.push(pricePerSqm);
                        }
                    }
                }
            }
        });
    }
    
    // Вычисляем средние стоимости: по типам и общую за м² по каждому ЖК
    statsByObject.forEach((stat, name) => {
        Object.keys(stat.byType).forEach(areaType => {
            const typeData = stat.byType[areaType];
            if (typeData.costs && typeData.costs.length > 0) {
                typeData.avgCost = typeData.costs.reduce((a, b) => a + b, 0) / typeData.costs.length;
            } else {
                typeData.avgCost = 0;
            }
        });
        
        if (stat.perSqm && stat.perSqm.length > 0) {
            stat.avgPerSqm = stat.perSqm.reduce((a, b) => a + b, 0) / stat.perSqm.length;
        } else {
            stat.avgPerSqm = 0;
        }
    });

    // Список ЖК (колонки) с привязанной статистикой по количеству квартир
    const objects = chars.map(item => {
        const name = item['Название ЖК'] || '';
        const stats = statsByObject.get(name) || { total: 0, byType: {} };
        return {
            name,
            is_main: !!item.is_main,
            data: item,
            stats
        };
    });

    const fields = [
        { key: 'Застройщик', label: 'Застройщик' },
        { key: 'Район', label: 'Район' },
        { key: 'Класс', label: 'Класс' },
        { key: 'Этажность', label: 'Этажность' },
        { key: 'Срок сдачи', label: 'Срок сдачи' },
        { key: 'Тип дома', label: 'Тип дома' },
        { key: 'Отделка', label: 'Отделка' }
    ];

    const table = document.createElement('table');
    table.className = 'groups-table';
    table.style.tableLayout = 'auto';
    table.style.width = '100%';
    table.style.minWidth = '100%';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    // Первый столбец — названия параметров
    const firstHeader = document.createElement('th');
    firstHeader.textContent = '';
    firstHeader.style.minWidth = '150px';
    firstHeader.style.maxWidth = '200px';
    firstHeader.style.width = 'auto';
    headerRow.appendChild(firstHeader);

    // Остальные заголовки — названия ЖК
    objects.forEach(obj => {
        const th = document.createElement('th');
        th.textContent = obj.name;
        th.style.whiteSpace = 'normal';
        th.style.wordBreak = 'break-word';
        if (obj.is_main) {
            th.classList.add('main-object-cell');
            th.style.backgroundColor = '#E8F5E9'; // мягкий зелёный фон
        }
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    // Для каждого параметра создаём строку,
    // каждая колонка соответствует конкретному ЖК
    fields.forEach(fieldInfo => {
        const row = document.createElement('tr');

        const labelCell = document.createElement('td');
        labelCell.textContent = fieldInfo.label;
        labelCell.style.fontWeight = 'bold';
        labelCell.style.textAlign = 'left';
        labelCell.style.paddingLeft = '8px';
        labelCell.style.whiteSpace = 'normal';
        labelCell.style.wordWrap = 'break-word';
        labelCell.style.overflowWrap = 'break-word';
        labelCell.style.fontSize = '0.75em';
        row.appendChild(labelCell);

        objects.forEach(obj => {
            const cell = document.createElement('td');
            const value = obj.data[fieldInfo.key] || '';
            cell.textContent = value;
            cell.style.whiteSpace = 'normal';
            cell.style.wordBreak = 'break-word';
            cell.style.fontSize = '0.75em';
            if (obj.is_main) {
                cell.classList.add('main-object-row');
                cell.style.backgroundColor = '#E8F5E9';
            }
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    // Блок "Квартирография"
    const sepRow = document.createElement('tr');
    const sepCell = document.createElement('td');
    sepCell.textContent = 'Квартирография';
    sepCell.colSpan = objects.length + 1;
    sepCell.style.fontWeight = 'bold';
    sepCell.style.backgroundColor = '#F5F5F5';
    sepRow.appendChild(sepCell);
    tbody.appendChild(sepRow);

    // Строка "Всего квартир"
    const totalRow = document.createElement('tr');
    const totalLabelCell = document.createElement('td');
    totalLabelCell.textContent = 'Всего квартир (шт.)';
    totalLabelCell.style.fontWeight = 'bold';
    totalLabelCell.style.textAlign = 'left';
    totalLabelCell.style.paddingLeft = '8px';
    totalLabelCell.style.whiteSpace = 'normal';
    totalLabelCell.style.wordWrap = 'break-word';
    totalLabelCell.style.overflowWrap = 'break-word';
    totalLabelCell.style.fontSize = '0.75em';
    totalRow.appendChild(totalLabelCell);

        objects.forEach(obj => {
            const cell = document.createElement('td');
            const total = obj.stats.total || 0;
            cell.textContent = total > 0 ? total : '';
            cell.style.whiteSpace = 'normal';
            cell.style.wordBreak = 'break-word';
            cell.style.fontSize = '0.75em';
            if (obj.is_main) {
                cell.classList.add('main-object-row');
                cell.style.backgroundColor = '#E8F5E9';
            }
            totalRow.appendChild(cell);
        });

    tbody.appendChild(totalRow);

    // Строки по типам комнатности (XS, 1к, S и т.д.)
    const areaTypesForSummary = AREA_TYPE_ORDER.slice(); // используем тот же порядок

    // Собираем все значения для цветового кодирования по столбцам
    const columnCountValues = {}; // obj.name -> [{ value, cell }]
    const columnCostValues = {}; // obj.name -> [{ value, cell }]
    objects.forEach(obj => {
        columnCountValues[obj.name] = [];
        columnCostValues[obj.name] = [];
    });

    areaTypesForSummary.forEach(areaType => {
        const row = document.createElement('tr');
        const labelCell = document.createElement('td');
        labelCell.textContent = areaType;
        labelCell.style.textAlign = 'left';
        labelCell.style.paddingLeft = '8px';
        labelCell.style.whiteSpace = 'normal';
        labelCell.style.wordWrap = 'break-word';
        labelCell.style.fontSize = '0.75em';
        row.appendChild(labelCell);

        objects.forEach(obj => {
            const cell = document.createElement('td');
            const total = obj.stats.total || 0;
            const typeData = obj.stats.byType && obj.stats.byType[areaType];
            const count = typeData ? (typeData.count || 0) : 0;
            
            if (count > 0 && total > 0) {
                const percent = Math.round((count / total) * 100);
                cell.textContent = `${count} (${percent}%)`;
                columnCountValues[obj.name].push({ value: count, cell: cell });
            } else {
                cell.textContent = '';
            }
            cell.style.whiteSpace = 'normal';
            cell.style.wordBreak = 'break-word';
            cell.style.fontSize = '0.75em';
            if (obj.is_main) {
                cell.classList.add('main-object-row');
                // Фон для основного ЖК будет применен после цветового кодирования
            }
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    // Добавляем строку "Средняя стоимость за м²" как агрегированную по всем типам
    const avgCostHeaderRow = document.createElement('tr');
    const avgCostHeaderCell = document.createElement('td');
    avgCostHeaderCell.textContent = 'Средняя стоимость за м² (руб./м²)';
    avgCostHeaderCell.style.fontWeight = 'bold';
    avgCostHeaderCell.style.textAlign = 'left';
    avgCostHeaderCell.style.paddingLeft = '8px';
    avgCostHeaderCell.style.whiteSpace = 'normal';
    avgCostHeaderCell.style.wordWrap = 'break-word';
    avgCostHeaderCell.style.fontSize = '0.75em';
    avgCostHeaderRow.appendChild(avgCostHeaderCell);

    objects.forEach(obj => {
        const cell = document.createElement('td');
        const stats = statsByObject.get(obj.name);
        const avgPerSqm = stats && stats.avgPerSqm ? stats.avgPerSqm : 0;
        
        if (avgPerSqm > 0) {
            cell.textContent = formatPrice(avgPerSqm);
            // Добавляем в набор для цветового кодирования по стоимости
            columnCostValues[obj.name].push({ value: avgPerSqm, cell: cell });
        } else {
            cell.textContent = '';
        }
        
        cell.style.whiteSpace = 'normal';
        cell.style.wordBreak = 'break-word';
        cell.style.fontSize = '0.75em';
        if (obj.is_main) {
            cell.classList.add('main-object-row');
            // Базовый фон будет учтен при цветовом кодировании
        }
        avgCostHeaderRow.appendChild(cell);
    });
    tbody.appendChild(avgCostHeaderRow);

    // Строки со средней стоимостью по типам квартир (в том же формате как количество)
    areaTypesForSummary.forEach(areaType => {
        const row = document.createElement('tr');
        const labelCell = document.createElement('td');
        labelCell.textContent = areaType;
        labelCell.style.textAlign = 'left';
        labelCell.style.paddingLeft = '8px';
        labelCell.style.whiteSpace = 'normal';
        labelCell.style.wordWrap = 'break-word';
        labelCell.style.fontSize = '0.75em';
        row.appendChild(labelCell);

        objects.forEach(obj => {
            const cell = document.createElement('td');
            const stats = statsByObject.get(obj.name);
            const typeData = stats && stats.byType && stats.byType[areaType];
            
            if (typeData && typeData.avgCost && typeData.avgCost > 0) {
                const formattedCost = formatPrice(typeData.avgCost);
                cell.textContent = formattedCost;
                columnCostValues[obj.name].push({ value: typeData.avgCost, cell: cell });
            } else {
                cell.textContent = '';
            }
            
            cell.style.whiteSpace = 'normal';
            cell.style.wordBreak = 'break-word';
            cell.style.fontSize = '0.75em';
            if (obj.is_main) {
                cell.classList.add('main-object-row');
                // Фон для основного ЖК будет применен после цветового кодирования
            }
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    // Применяем цветовое кодирование внутри каждого столбца для количества
    objects.forEach(obj => {
        const colData = columnCountValues[obj.name];
        if (colData && colData.length > 0) {
            const countValues = colData.map(item => item.value).filter(v => v > 0);
            if (countValues.length > 1) { // Нужно минимум 2 значения для градиента
                const minCount = Math.min(...countValues);
                const maxCount = Math.max(...countValues);
                const range = maxCount - minCount;
                
                if (range > 0) {
                    colData.forEach(item => {
                        if (item.value > 0) {
                            const intensity = (item.value - minCount) / range;
                            // Легкое цветовое кодирование: от почти белого к светло-голубому
                            const r = Math.round(240 + intensity * 15); // 240-255
                            const g = Math.round(248 + intensity * 7);  // 248-255
                            const b = Math.round(255);
                            // Смешиваем с базовым цветом для основного ЖК
                            if (obj.is_main) {
                                // Для основного ЖК делаем более светлый оттенок
                                const mixR = Math.round(232 + intensity * 8);
                                const mixG = Math.round(245 + intensity * 4);
                                const mixB = Math.round(233 + intensity * 22);
                                item.cell.style.backgroundColor = `rgb(${mixR}, ${mixG}, ${mixB})`;
                            } else {
                                item.cell.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
                            }
                        }
                    });
                }
            } else if (obj.is_main && countValues.length === 1) {
                // Если только одно значение и это основной ЖК, применяем базовый фон
                colData.forEach(item => {
                    if (item.value > 0) {
                        item.cell.style.backgroundColor = '#E8F5E9';
                    }
                });
            }
        }
    });

    // Применяем цветовое кодирование внутри каждого столбца для стоимости
    objects.forEach(obj => {
        const colData = columnCostValues[obj.name];
        if (colData && colData.length > 0) {
            const costValues = colData.map(item => item.value).filter(v => v > 0);
            if (costValues.length > 1) { // Нужно минимум 2 значения для градиента
                const minCost = Math.min(...costValues);
                const maxCost = Math.max(...costValues);
                const range = maxCost - minCost;
                
                if (range > 0) {
                    colData.forEach(item => {
                        if (item.value > 0) {
                            const intensity = (item.value - minCost) / range;
                            // Легкое цветовое кодирование: от почти белого к светло-желтому
                            const r = Math.round(255);
                            const g = Math.round(250 + intensity * 5);  // 250-255
                            const b = Math.round(240 + intensity * 15);   // 240-255
                            if (obj.is_main) {
                                // Для основного ЖК смешиваем с зеленым фоном
                                const mixR = Math.round(232 + intensity * 23);
                                const mixG = Math.round(245 + intensity * 10);
                                const mixB = Math.round(233 + intensity * 22);
                                item.cell.style.backgroundColor = `rgb(${mixR}, ${mixG}, ${mixB})`;
                            } else {
                                item.cell.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
                            }
                        }
                    });
                }
            } else if (obj.is_main && costValues.length === 1) {
                // Если только одно значение и это основной ЖК, применяем базовый фон
                colData.forEach(item => {
                    if (item.value > 0) {
                        item.cell.style.backgroundColor = '#E8F5E9';
                    }
                });
            }
        }
    });

    table.appendChild(tbody);
    groupsList.appendChild(table);
}

// Проверка наличия сопоставимых групп
function checkComparableGroups(groups) {
    for (let i = 0; i < groups.length; i++) {
        for (let j = i + 1; j < groups.length; j++) {
            const g1 = groups[i];
            const g2 = groups[j];
            
            // Сопоставимые группы: одинаковый тип площади, разные источники
            if (g1.тип_площади === g2.тип_площади &&
                g1.source !== g2.source) {
                return true;
            }
        }
    }
    return false;
}

// Отображение результатов сравнения
function displayComparisons(comparisons) {
    const comparisonsList = document.getElementById('comparisonsList');
    const comparisonSection = document.getElementById('comparisonSection');
    
    comparisonsList.innerHTML = '';
    
    if (comparisons.length === 0) {
        comparisonsList.innerHTML = '<p>Сопоставимые группы не найдены</p>';
        return;
    }
    
    comparisons.forEach((comparison, index) => {
        const item = document.createElement('div');
        item.className = 'comparison-item';
        
        const params = comparison.parameters;
        const stats1 = comparison.group1.stats;
        const stats2 = comparison.group2.stats;
        const percentageDiffs = comparison.percentage_diffs || {};
        const mainSource = comparison.main_source || comparison.group1.source;
        
        // Определяем, какая группа - основной ЖК
        const isGroup1Main = comparison.group1.source === mainSource;
        const mainStats = isGroup1Main ? stats1 : stats2;
        const compStats = isGroup1Main ? stats2 : stats1;
        const mainSourceName = isGroup1Main ? comparison.group1.source : comparison.group2.source;
        const compSourceName = isGroup1Main ? comparison.group2.source : comparison.group1.source;
        
        const groupTitle = `Тип площади: ${params.тип_площади}`;
        
        // Функция для форматирования ячейки с процентом
        function formatCellWithPercentage(value, percentageDiff, isMain) {
            if (!isMain || percentageDiff === null || percentageDiff === undefined) {
                return `${formatPrice(value)} руб.`;
            }
            
            const sign = percentageDiff > 0 ? '+' : '';
            const color = percentageDiff < 0 ? 'green' : 'red'; // Зеленый если дешевле (отрицательный %), красный если дороже
            const percentageText = ` (${sign}${percentageDiff.toFixed(2)}%)`;
            
            return `${formatPrice(value)} руб.<span class="percentage-diff ${color}">${percentageText}</span>`;
        }
        
        item.innerHTML = `
            <h3 class="comparison-title">${groupTitle}</h3>
            
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Показатель</th>
                        <th>${mainSourceName}</th>
                        <th>${compSourceName}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Среднее</strong></td>
                        <td>${formatCellWithPercentage(mainStats.mean, percentageDiffs.mean, true)}</td>
                        <td>${formatPrice(compStats.mean)} руб.</td>
                    </tr>
                    <tr>
                        <td><strong>Медиана</strong></td>
                        <td>${formatCellWithPercentage(mainStats.median, percentageDiffs.median, true)}</td>
                        <td>${formatPrice(compStats.median)} руб.</td>
                    </tr>
                    <tr>
                        <td><strong>Минимум</strong></td>
                        <td>${formatCellWithPercentage(mainStats.min, percentageDiffs.min, true)}</td>
                        <td>${formatPrice(compStats.min)} руб.</td>
                    </tr>
                    <tr>
                        <td><strong>Максимум</strong></td>
                        <td>${formatCellWithPercentage(mainStats.max, percentageDiffs.max, true)}</td>
                        <td>${formatPrice(compStats.max)} руб.</td>
                    </tr>
                    <tr>
                        <td><strong>Выбросы (всего)</strong></td>
                        <td>${mainStats.outliers_count || 0}</td>
                        <td>${compStats.outliers_count || 0}</td>
                    </tr>
                    <tr>
                        <td><strong>Выбросы снизу</strong></td>
                        <td>${mainStats.outliers_lower_count || 0}${mainStats.outliers_lower && mainStats.outliers_lower.length > 0 ? `<br><span class="outliers-values">${mainStats.outliers_lower.map(v => formatPrice(v)).join(', ')}</span>` : ''}</td>
                        <td>${compStats.outliers_lower_count || 0}${compStats.outliers_lower && compStats.outliers_lower.length > 0 ? `<br><span class="outliers-values">${compStats.outliers_lower.map(v => formatPrice(v)).join(', ')}</span>` : ''}</td>
                    </tr>
                    <tr>
                        <td><strong>Выбросы сверху</strong></td>
                        <td>${mainStats.outliers_upper_count || 0}${mainStats.outliers_upper && mainStats.outliers_upper.length > 0 ? `<br><span class="outliers-values">${mainStats.outliers_upper.map(v => formatPrice(v)).join(', ')}</span>` : ''}</td>
                        <td>${compStats.outliers_upper_count || 0}${compStats.outliers_upper && compStats.outliers_upper.length > 0 ? `<br><span class="outliers-values">${compStats.outliers_upper.map(v => formatPrice(v)).join(', ')}</span>` : ''}</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="charts-container">
                <div class="chart-box">
                    <h4>Boxplot</h4>
                    ${comparison.boxplot ? `<img src="data:image/png;base64,${comparison.boxplot}" alt="Boxplot">` : '<p>График недоступен</p>'}
                </div>
                <div class="chart-box">
                    <h4>Гистограмма</h4>
                    ${comparison.histogram ? `<img src="data:image/png;base64,${comparison.histogram}" alt="Histogram">` : '<p>График недоступен</p>'}
                </div>
            </div>
        `;
        
        comparisonsList.appendChild(item);
    });
    
    comparisonSection.style.display = 'block';
    comparisonSection.scrollIntoView({ behavior: 'smooth' });
}

// Вспомогательные функции
function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU').format(Math.round(price));
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

