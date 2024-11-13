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
    return !readActivities[activity._id];
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

function createActivityElement(activity) {
    const div = document.createElement('div');
    const isNew = isActivityNew(activity);
    
    div.className = `activity-item p-4 border rounded-lg transition-colors ${
        isNew ? 'border-blue-400 bg-blue-50' : 'border-gray-200'
    } hover:bg-gray-50`;
    
    div.setAttribute('data-activity-id', activity._id);

    const relativeDate = formatRelativeDate(activity.created_at);

    div.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                ${isNew ? '<span class="inline-block px-2 py-1 text-xs bg-blue-500 text-white rounded-full">Nowe</span>' : ''}
                <h3 class="text-lg font-semibold text-gray-800">${activity.title}</h3>
            </div>
            <span class="text-sm text-gray-500">${relativeDate}</span>
        </div>
        <div class="mt-2">
            ${activity.url ? `<a href="${activity.url}" target="_blank" class="text-blue-600 hover:text-blue-800">Otwórz →</a>` : ''}
        </div>
    `;

    // Dodaj obsługę zdarzeń dla oznaczania jako przeczytane
    div.addEventListener('click', () => {
        if (isNew) {
            markActivityAsRead(activity._id);
            div.classList.remove('border-blue-400', 'bg-blue-50');
            div.classList.add('border-gray-200');
            const newBadge = div.querySelector('.bg-blue-500');
            if (newBadge) {
                newBadge.remove();
            }
        }
    });

    // Dodaj też obsługę najechania myszką
    div.addEventListener('mouseenter', () => {
        if (isNew) {
            markActivityAsRead(activity._id);
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
