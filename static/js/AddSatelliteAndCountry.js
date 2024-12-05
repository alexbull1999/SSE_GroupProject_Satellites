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
    const tableBody = document.querySelector("tbody");
    tableBody.innerHTML = satellites.map(satellite => `
        <tr>
            <td class="p-3 text-gray-400">
                <a href="/satellite/${satellite.id}" class="text-indigo-500 hover:text-indigo-700">
                    ${satellite.name}
                </a>
            </td>
            <td class="p-3">
                <button onclick="deleteSatellite('${satellite.name}')">Delete</button>
            </td>
        </tr>
    `).join("");
     // Reattach event listeners after the table is updated
     const deleteButtons = tableBody.querySelectorAll("button");
     deleteButtons.forEach(button => {
         button.addEventListener("click", (e) => {
             const satelliteName = e.target.closest('tr').querySelector('a').textContent;
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
    const tableBody = document.querySelector("#country-table tbody");
    tableBody.innerHTML = countries.map(country => `
        <tr>
            <td class="p-3 text-gray-400">
                <a href="/country/${country.name}" class="text-indigo-500 hover:text-indigo-700">
                    ${country.name}
                </a>
            </td>
            <td class="p-3">
                <button onclick="deleteCountry('${country.name}')">Delete</button>
            </td>
        </tr>
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
