async function searchCountry() {
    const query = document.getElementById('country-search-bar').value.trim();
    const dropdown = document.getElementById('country-dropdown');

    //Wait for at least 2 characters to be typed
    if (query.length < 2) {
        dropdown.innerHTML = '';
        dropdown.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/country_search?query=${encodeURIComponent(query)}`);
        const countries = await response.json();

        dropdown.innerHTML = ''; //Clear previous results
        dropdown.style.display = 'none'; //Hide if no results

        if (countries.length > 0) {
            countries.forEach(country => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.textContent = country[3] // Country name

                //Handle click to autofill search bar
                item.onclick = () => {
                    document.getElementById('country-search-bar').value = country[3];
                    dropdown.innerHTML = '';
                    dropdown.style.display = 'none'; //Hide dropdown again
                    document.getElementById('country-form').submit();
                };

                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block'; //show dropdown
        }
    } catch (error) {
        console.error('Error fetching countries:', error)
    }
}

async function searchSatellite() {
    const query = document.getElementById('search-bar').value.trim();
    const dropdown = document.getElementById('dropdown')

    //wait for at least 2 characters to be typed
    if (query.length < 2) {
        dropdown.innerHTML = '';
        dropdown.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
        const satellites = await response.json();

        dropdown.innerHTML = ''; //Clear previous results
        dropdown.style.display = 'none'; //hide if no results

        if (satellites.length > 0) {
            satellites.forEach(satellite => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.textContent = satellite[1]; //satellite name

                // handle click to autofill search bar
                item.onclick = () => {
                    document.getElementById('search-bar').value = satellite[1];
                    dropdown.innerHTML = '';
                    dropdown.style.display = 'none'; //hide the dropdown again
                    document.getElementById('satellite-form').submit(); // Submit the form
                };

                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block'; //show the dropdown
        }
    } catch (error) {
        console.error('Error fetching satellites:', error);
    }
}

