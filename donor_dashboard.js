document.addEventListener("DOMContentLoaded", function () {
    const requestsList = document.getElementById("requests");
    const locationFilter = document.getElementById("location-filter");
    const applyFilterBtn = document.getElementById("apply-filter");

    // Function to fetch food requests from localStorage
    function getFoodRequests() {
        return JSON.parse(localStorage.getItem("foodRequests")) || [];
    }

    // Function to save updated food requests to localStorage
    function saveFoodRequests(requests) {
        localStorage.setItem("foodRequests", JSON.stringify(requests));
    }

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
                                  ${request.description} <br>
                                  <button class="accept-request" data-id="${request.id}">Accept Request</button>`;
            requestsList.appendChild(listItem);
        });

        // Attach event listeners to "Accept Request" buttons
        document.querySelectorAll(".accept-request").forEach(button => {
            button.addEventListener("click", function () {
                const requestId = this.getAttribute("data-id");
                acceptRequest(requestId);
            });
        });
    }

    // Function to accept a food request
    function acceptRequest(requestId) {
        let foodRequests = getFoodRequests();
        foodRequests = foodRequests.filter(request => request.id != requestId);
        saveFoodRequests(foodRequests); // Update localStorage
        displayRequests(foodRequests);
        alert("You have successfully accepted the request!");
    }

    // Filter requests by location
    applyFilterBtn.addEventListener("click", function () {
        const filterValue = locationFilter.value.trim().toLowerCase();
        const foodRequests = getFoodRequests();
        const filteredRequests = foodRequests.filter(request =>
            request.location.toLowerCase().includes(filterValue)
        );
        displayRequests(filteredRequests);
    });

    // Function to remove expired requests periodically
    function removeExpiredRequests() {
        let foodRequests = getFoodRequests();
        const currentTime = new Date().getTime();
        foodRequests = foodRequests.filter(request => new Date(request.expiryTime).getTime() > currentTime);
        saveFoodRequests(foodRequests);
        displayRequests(foodRequests);
    }

    // Check for expired requests every minute
    setInterval(removeExpiredRequests, 60000);

    // Initial load: fetch requests from storage and display them
    displayRequests(getFoodRequests());
});