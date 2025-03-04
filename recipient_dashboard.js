document.addEventListener("DOMContentLoaded", function () {
    const requestForm = document.getElementById("requestForm");
    const requestsList = document.getElementById("requests");
    const locationFilter = document.getElementById("location-filter");
    const applyFilterBtn = document.getElementById("apply-filter");

    // Array to store food requests
    let foodRequests = [];

    // Function to display food requests
    function displayRequests(filteredRequests) {
        requestsList.innerHTML = ""; // Clear the list
        const currentTime = new Date().getTime();

        filteredRequests.forEach(request => {
            const expiryTime = new Date(request.expiryTime).getTime();
            if (expiryTime < currentTime) return; // Skip expired requests

            const listItem = document.createElement("li");
            listItem.innerHTML = `<strong>${request.foodItem}</strong> - ${request.quantity} servings <br>
                                  <strong>Location:</strong> ${request.location} <br>
                                  <strong>Expiry:</strong> <span class="expiry-time">${request.expiryTime}</span><br>
                                  ${request.description}`;
            requestsList.appendChild(listItem);
        });
    }

    // Handle form submission
    requestForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const foodItem = document.getElementById("foodItem").value.trim();
        const quantity = document.getElementById("quantity").value.trim();
        const location = document.getElementById("location").value.trim();
        const expiryTime = document.getElementById("expiryTime").value.trim();
        const description = document.getElementById("description").value.trim();

        if (foodItem && quantity && location && expiryTime) {
            // Add new request to the list
            const newRequest = { foodItem, quantity, location, expiryTime, description };
            foodRequests.push(newRequest);
            displayRequests(foodRequests); // Refresh list
            requestForm.reset();
        } else {
            alert("Please fill in all required fields.");
        }
    });

    // Filter requests by location
    applyFilterBtn.addEventListener("click", function () {
        const filterValue = locationFilter.value.trim().toLowerCase();
        const filteredRequests = foodRequests.filter(request =>
            request.location.toLowerCase().includes(filterValue)
        );
        displayRequests(filteredRequests);
    });

    // Function to remove expired requests periodically
    function removeExpiredRequests() {
        const currentTime = new Date().getTime();
        foodRequests = foodRequests.filter(request => new Date(request.expiryTime).getTime() > currentTime);
        displayRequests(foodRequests);
    }

    // Check for expired requests every minute
    setInterval(removeExpiredRequests, 60000);

    // Initial load: display all requests
    displayRequests(foodRequests);
});
