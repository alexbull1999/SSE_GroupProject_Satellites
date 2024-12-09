//Satellite functions

// Function to add selected satellite to tracking list - maybe move this function and the ones below to the account.js
function addSatelliteToTracking() {
    console.log("adding satellite...")
    const searchBar = document.getElementById("search-bar");
    const satelliteName = searchBar.value.trim();

    console.log("Satellite Name:", satelliteName); // Debugging line

    if (!satelliteName) {
        alert("Please select a satellite.");
        return;
    }

    const username = document.querySelector("input[name='username']").value; // Get the username from the hidden input field

    // Send the satellite name and username to the server
    fetch("/add_satellite", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            'username': username,
            'satellite_name': satelliteName
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json(); // Assuming the server responds with the updated satellite list
        } else {
            throw new Error("Failed to add satellite.");
        }
    })
    .then(updatedSatellites => {
        updateSatellitesTable(updatedSatellites); // Refresh the satellite list/table
        searchBar.value = ""; // Clear the search bar
    })
    .catch(error => {
        console.error("Error adding satellite:", error);
    });
}

function deleteSatellite(satelliteName) {
    console.log("Deleting satellite with ID:", satelliteName);

    const username = document.querySelector("input[name='username']").value;

    fetch("/delete_satellite", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            'username': username,
            'satellite_name': satelliteName
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error("Failed to delete satellite.");
        }
    })
    .then(updatedSatellites => {
        // Call the function to update the table with the new satellite list
        updateSatellitesTable(updatedSatellites);
        console.log("Satellite deleted successfully");
    })
    .catch(error => {
        console.error("Error deleting satellite:", error);
    });
}


// Function to update the satellite list/table
function updateSatellitesTable(satellites) {
    const container = document.querySelector(".satellites-grid"); // Select the grid container
    container.innerHTML = satellites.map(satellite => `
        <div class="w-[272px] max-w-full bg-white py-8 px-4 rounded-lg shadow-lg flex items-center justify-center mx-auto">
            <a href="/satellites/${satellite.name}" class="flex-1 text-left">
                <h3 class="text-xl font-medium text-gray-600">${satellite.name}</h3>
                <p class="text-gray-400">ID: ${satellite.id}</p>
            </a>
            <button
                onclick="deleteSatellite('${satellite.name}')"
                class="text-red-500 hover:text-red-700">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                </svg>
            </button>
        </div>
    `).join("");

    // Attach event listeners to the delete buttons
    const deleteButtons = container.querySelectorAll("button");
    deleteButtons.forEach(button => {
        button.addEventListener("click", (e) => {
            const satelliteName = e.target.closest('div').querySelector('h3').textContent;
            deleteSatellite(satelliteName);
        });
    });
}


//country tables
// Function to add selected satellite to tracking list - maybe move this function and the ones below to the account.js
function addCountryToTracking() {
    console.log("Adding country...");
    const countrySearchBar = document.getElementById("country-search-bar");
    const countryName = countrySearchBar.value.trim();

    console.log("Country Name:", countryName); // Debugging line

    if (!countryName) {
        alert("Please select a country.");
        return;
    }

    const username = document.querySelector("input[name='username']").value; // Get the username from the hidden input field

    // Send the country name and username to the server
    fetch("/add_country", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            'username': username,
            'country_name': countryName
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json(); // Assuming the server responds with the updated country list
        } else {
            throw new Error("Failed to add country.");
        }
    })
    .then(updatedCountries => {
        updateCountriesTable(updatedCountries); // Refresh the country list/table
        countrySearchBar.value = ""; // Clear the search bar
    })
    .catch(error => {
        console.error("Error adding country:", error);
    });
}


/// Function to delete a country from the tracking list - now uses country name
function deleteCountry(countryName) {
    console.log("Deleting country:", countryName);

    const username = document.querySelector("input[name='username']").value;

    fetch("/delete_country", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            'username': username,
            'country_name': countryName
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error("Failed to delete country.");
        }
    })
    .then(updatedCountries => {
        // Call the function to update the table with the new country list
        updateCountriesTable(updatedCountries);
        console.log("Country deleted successfully");
    })
    .catch(error => {
        console.error("Error deleting country:", error);
    });
}



// Function to update the country list/table
function updateCountriesTable(countries) {
    const tableBody = document.querySelector(".countries-grid");
    tableBody.innerHTML = countries.map(country => `
        <div class="w-60 bg-white py-8 px-4 rounded-lg shadow-lg flex items-center justify-center mx-auto">
            <a onclick="getCountryDetails('${country.name}')" class="flex-1 text-left">
                <h3 class="text-xl font-medium text-gray-600">
                ${country.name}
                </h3>
            </a>
            <button
                onclick="deleteCountry('${country.name}')"
                class="text-red-500 hover:text-red-700">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                </svg>
            </button>
        </div>
    `).join("");
     // Attach event listeners for delete buttons
    const deleteButtons = tableBody.querySelectorAll(".delete-button");
    deleteButtons.forEach(button => {
        button.addEventListener("click", (e) => {
            const countryName = e.target.getAttribute("data-country");
            deleteCountry(countryName); // Call the delete function
        });
    });
}

