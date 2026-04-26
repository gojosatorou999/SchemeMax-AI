document.addEventListener('DOMContentLoaded', () => {
    // Check if we need to load translations client-side
    const langSelect = document.getElementById('lang-select');
    if (!langSelect) return;
    
    const currentLang = langSelect.value;
    if (currentLang === 'en') return; // Default language, no need to fetch if rendered server-side
    
    // Fetch translations
    fetch(`/api/translations/${currentLang}`)
        .then(res => res.json())
        .then(translations => {
            // Apply translations to elements with data-i18n attribute
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (translations[key]) {
                    el.textContent = translations[key];
                }
            });
        })
        .catch(err => console.error('Failed to load translations:', err));
});
