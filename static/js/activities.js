// Funkcje pomocnicze do obsługi przeczytanych aktywności
function getReadActivities() {
    const readActivities = localStorage.getItem('readActivities');
    return readActivities ? JSON.parse(readActivities) : {};
}

function markActivityAsRead(activityId) {
    const readActivities = getReadActivities();
    readActivities[activityId] = Date.now();
    localStorage.setItem('readActivities', JSON.stringify(readActivities));
}

function isActivityNew(activity) {
    const readActivities = getReadActivities();
    return !readActivities[activity.id]; // Zmiana z _id na id
}

// Funkcja formatująca względną datę
function formatRelativeDate(date) {
    const now = new Date();
    const activityDate = new Date(date);
    const diffTime = Math.abs(now - activityDate);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return 'dzisiaj';
    } else if (diffDays === 1) {
        return 'wczoraj';
    } else {
        return `${diffDays} dni temu`;
    }
}

async function fetchActivities() {
    try {
        const response = await axios.get('/api/activities?limit=10');
        const activities = response.data.activities;
        displayActivities(activities);
    } catch (error) {
        console.error('Błąd podczas pobierania aktywności:', error);
        displayError();
    }
}

function displayActivities(activities) {
    const container = document.getElementById('activities-list');
    container.innerHTML = '';

    activities.forEach(activity => {
        const activityElement = createActivityElement(activity);
        container.appendChild(activityElement);
    });
}

function getContentHtml(activity) {
    // Jeśli content jest obiektem z html/text
    if (activity.content && typeof activity.content === 'object' && (activity.content.html || activity.content.text)) {
        return activity.content.html || activity.content.text;
    }
    
    // Jeśli mamy content_html lub content_text z API
    if (activity.content_html || activity.content_text) {
        return activity.content_html || activity.content_text;
    }
    
    // Jeśli content jest bezpośrednio stringiem
    if (activity.content && typeof activity.content === 'string') {
        return activity.content;
    }
    
    return '';
}

function createActivityElement(activity) {
    const div = document.createElement('div');
    const isNew = isActivityNew(activity);
    
    div.className = `activity-item p-4 border rounded-lg transition-colors ${
        isNew ? 'border-blue-400 bg-blue-50' : 'border-gray-200'
    } ${activity.type === 'resource' ? '' : 'hover:bg-gray-50 cursor-pointer'}`;
    
    div.setAttribute('data-activity-id', activity.id);
    div.setAttribute('data-expanded', 'false');

    const relativeDate = formatRelativeDate(activity.created_at);

    // Przygotowanie sekcji z obrazami jeśli istnieją
    const imagesHtml = activity.images && activity.images.length > 0 ? `
        <div class="images-section mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            ${activity.images.map(img => `
                <img 
                    src="${img.src}" 
                    alt="${img.alt}" 
                    class="max-w-full h-auto rounded shadow-sm"
                    style="max-height: 300px; object-fit: contain;"
                />
            `).join('')}
        </div>
    ` : '';

    div.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                ${isNew ? '<span class="inline-block px-2 py-1 text-xs bg-blue-500 text-white rounded-full">Nowe</span>' : ''}
                <h3 class="text-lg font-semibold text-gray-800">${activity.title}</h3>
            </div>
            <span class="text-sm text-gray-500">${relativeDate}</span>
        </div>
        ${activity.type === 'resource' ? `
            <div class="mt-2">
                <a href="${activity.url}" target="_blank" class="inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">Otwórz →</a>
            </div>
        ` : `
            <div class="content-section mt-2 hidden">
                <div class="prose max-w-none">
                    ${getContentHtml(activity)}
                    ${imagesHtml}
                </div>
            </div>
            ${activity.url ? `
                <div class="mt-2">
                    <a href="${activity.url}" target="_blank" class="text-blue-600 hover:text-blue-800">Otwórz →</a>
                </div>
            ` : ''}
        `}
    `;


    // Obsługa zdarzeń tylko dla typów page i label
    if (activity.type !== 'resource') {
        div.addEventListener('click', (e) => {
            // Ignoruj kliknięcia w linki
            if (e.target.tagName === 'A') {
                return;
            }

            if (isNew) {
                markActivityAsRead(activity.id);
                div.classList.remove('border-blue-400', 'bg-blue-50');
                div.classList.add('border-gray-200');
                const newBadge = div.querySelector('.bg-blue-500');
                if (newBadge) {
                    newBadge.remove();
                }
            }

            // Obsługa rozwijania/zwijania zawartości
            const contentSection = div.querySelector('.content-section');
            const isExpanded = div.getAttribute('data-expanded') === 'true';
            
            if (contentSection) {
                contentSection.classList.toggle('hidden');
                div.setAttribute('data-expanded', !isExpanded);
            }
        });
    } else {
        // Dla resource oznacz jako przeczytane przy najechaniu
        div.addEventListener('mouseenter', () => {
            if (isNew) {
                markActivityAsRead(activity.id);
                div.classList.remove('border-blue-400', 'bg-blue-50');
                div.classList.add('border-gray-200');
                const newBadge = div.querySelector('.bg-blue-500');
                if (newBadge) {
                    newBadge.remove();
                }
            }
        });
    }

    // Obsługa najechania myszką
    div.addEventListener('mouseenter', () => {
        if (isNew) {
            markActivityAsRead(activity.id); // Zmiana z _id na id
            div.classList.remove('border-blue-400', 'bg-blue-50');
            div.classList.add('border-gray-200');
            const newBadge = div.querySelector('.bg-blue-500');
            if (newBadge) {
                newBadge.remove();
            }
        }
    });

    return div;
}

function displayError() {
    const container = document.getElementById('activities-list');
    container.innerHTML = `
        <div class="text-center p-4 text-red-600">
            Wystąpił błąd podczas ładowania aktywności. Spróbuj odświeżyć stronę.
        </div>
    `;
}

// Pobierz aktywności przy załadowaniu strony
document.addEventListener('DOMContentLoaded', fetchActivities);

// Odświeżaj aktywności co 5 minut
setInterval(fetchActivities, 5 * 60 * 1000);
