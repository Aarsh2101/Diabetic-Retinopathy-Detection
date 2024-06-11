// Get the button
var updateButton = document.getElementById('update-user-button');

// Add an event listener for the click event
updateButton.addEventListener('click', updateUserInfo);

function updateUserInfo() {
    // Get the input fields
    var firstName = document.getElementById('specialist-first-name');
    var lastName = document.getElementById('specialist-last-name');
    var emailInput = document.getElementById('specialist-email');
    var affiliationInput = document.getElementById('specialist-affiliation');

    // Gather the values from the input fields
    var firstName = firstName.value;
    var lastName = lastName.value;
    var email = emailInput.value;
    var affiliation = affiliationInput.value;

    // Send the values to the server to update the user information
    fetch('/update_user_info/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            first_name: firstName,
            last_name: lastName,
            email: email,
            affiliation: affiliation,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Specialist information updated successfully');
        } else {
            console.error('Failed to upload image');
        }
    })
    .catch((error) => {
        // Handle any errors
        console.error('Error:', error);
    });
}