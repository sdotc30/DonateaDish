fetch("http://127.0.0.1:5000/recipient")  // Fetch users from API
  .then(response => response.json())  // Convert response to JSON
  .then(data => console.log("Recipient:", data))  // Print users in console
  .catch(error => console.error("Error fetching users:", error));
