async function searchCountry() {
    const query = document.getElementById('country-search-bar').value.trim();
    const dropdown = document.getElementById('country-dropdown');
    const inputField = document.getElementById('country-search-bar');

    // Wait for at least 2 characters to be typed
    if (query.length < 2) {
        dropdown.innerHTML = '';
        dropdown.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/country_search?query=${encodeURIComponent(query)}`);
        const countries = await response.json();

        dropdown.innerHTML = '';
        dropdown.style.display = 'none';

        if (countries.length > 0) {
            // Set dropdown width to match the input field
            dropdown.style.width = `${inputField.offsetWidth}px`;

            countries.forEach(country => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.textContent = country[3]; // Country name

                // Handle click to autofill search bar
                item.onclick = () => {
                    inputField.value = country[3];
                    dropdown.innerHTML = '';
                    dropdown.style.display = 'none';
                    document.getElementById('country-form').submit();
                };

                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
        }
    } catch (error) {
        console.error('Error fetching countries:', error);
    }
}

async function searchSatellite() {
    const query = document.getElementById('search-bar').value.trim();
    const dropdown = document.getElementById('dropdown');
    const inputField = document.getElementById('search-bar');

    if (query.length < 2) {
        dropdown.innerHTML = '';
        dropdown.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
        const satellites = await response.json();

        dropdown.innerHTML = '';
        dropdown.style.display = 'none';

        if (satellites.length > 0) {
            // Set dropdown width to match the input field
            dropdown.style.width = `${inputField.offsetWidth}px`;

            satellites.forEach(satellite => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.textContent = satellite[1];

                // Handle click to autofill search bar
                item.onclick = () => {
                    inputField.value = satellite[1];
                    dropdown.innerHTML = '';
                    dropdown.style.display = 'none';
                    document.getElementById('satellite-form').submit();
                };

                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
        }
    } catch (error) {
        console.error('Error fetching satellites:', error);
    }
}

// Function to close dropdown when clicking anywhere outside input or dropdown
document.addEventListener('click', (event) => {
    const searchBar = document.getElementById('search-bar');
    const dropdown = document.getElementById('dropdown');

    const countrySearchBar = document.getElementById('country-search-bar');
    const countryDropdown = document.getElementById('country-dropdown');

    // Close satellite dropdown if clicking outside the input or dropdown
    if (!searchBar.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.innerHTML = '';
        dropdown.style.display = 'none';
    }

    // Close country dropdown if clicking outside the input or dropdown
    if (!countrySearchBar.contains(event.target) && !countryDropdown.contains(event.target)) {
        countryDropdown.innerHTML = '';
        countryDropdown.style.display = 'none';
    }
});
