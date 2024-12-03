
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
                };

                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block'; //show the dropdown
        }
    } catch (error) {
        console.error('Error fetching satellites:', error);
    }
}


// Function to add selected satellite to tracking list
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
        </tr>
    `).join("");
}