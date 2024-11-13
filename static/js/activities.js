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
    div.className = 'activity-item p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors';

    const date = new Date(activity.created_at);
    const formattedDate = date.toLocaleDateString('pl-PL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    div.innerHTML = `
        <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-800">${activity.title}</h3>
            <span class="text-sm text-gray-500">${formattedDate}</span>
        </div>
        <div class="mt-2">
            <span class="inline-block px-2 py-1 text-sm rounded-full ${getTypeColor(activity.type)}">
                ${activity.type}
            </span>
            ${activity.url ? `<a href="${activity.url}" target="_blank" class="ml-2 text-blue-600 hover:text-blue-800">Otwórz →</a>` : ''}
        </div>
    `;

    return div;
}

function getTypeColor(type) {
    const colors = {
        'resource': 'bg-blue-100 text-blue-800',
        'assignment': 'bg-green-100 text-green-800',
        'forum': 'bg-yellow-100 text-yellow-800',
        'quiz': 'bg-purple-100 text-purple-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
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
