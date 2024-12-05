
// Function to handle account creation
function createAccount() {
    console.log("creatAccount function called");
    const username = document.getElementById('create-username').value;

    // Make a POST request to create the account
    fetch('/login/create_account', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username }),
    })
    .then(response => {
        if (response.ok) {
            // Redirect to the new account page after successful account creation
            window.location.href = `/account/${username}`;
        } else {
            alert("Error creating account");
        }
    })
    .catch(error => console.error('Error:', error));
}

// Function to handle login
function login() {
    const username = document.getElementById('login-username').value;

    // Make a POST request to log the user in
    fetch('/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username }),
    })
    .then(response => {
        if (response.ok) {
            // Redirect to the account page after successful login
            window.location.href = `/account/${username}`;
        } else {
            alert("Invalid username");
        }
    })
    .catch(error => console.error('Error:', error));
}