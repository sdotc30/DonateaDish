document.addEventListener("DOMContentLoaded", function () {
    const requestForm = document.getElementById("requestForm");
    const requestsList = document.getElementById("requests");
    const locationFilter = document.getElementById("location-filter");
    const applyFilterBtn = document.getElementById("apply-filter");

    let foodRequests = [];

    // ✅ Function to display food requests with real-time countdown
    function displayRequests() {
        requestsList.innerHTML = ""; // Clear the list

        const currentTime = new Date().getTime();

        foodRequests.forEach((request, index) => {
            const expiryTime = new Date(request.expiryTime).getTime();
            
            if (expiryTime < currentTime) {
                // Remove expired requests
                foodRequests.splice(index, 1);
                return;
            }

            const listItem = document.createElement("li");
            listItem.innerHTML = `
                <strong>${request.foodItem}</strong> - ${request.quantity} servings <br>
                <strong>Location:</strong> ${request.location} <br>
                <strong>Expiry:</strong> 
                <span class="expiry-time" data-expiry="${request.expiryTime}">
                </span><br>
                ${request.description}
            `;
            requestsList.appendChild(listItem);
        });

        // ✅ Start countdown timers for each request
        startCountdown();
    }

    // ✅ Function to start the real-time countdown
    function startCountdown() {
        const timers = document.querySelectorAll(".expiry-time");

        timers.forEach(timer => {
            const expiryTime = new Date(timer.dataset.expiry).getTime();

            function updateTimer() {
                const currentTime = new Date().getTime();
                const remainingTime = expiryTime - currentTime;

                if (remainingTime <= 0) {
                    timer.innerHTML = "⏳ Expired";
                    timer.parentElement.classList.add("expired");
                    return;
                }

                const hours = Math.floor((remainingTime / (1000 * 60 * 60)) % 24);
                const minutes = Math.floor((remainingTime / (1000 * 60)) % 60);
                const seconds = Math.floor((remainingTime / 1000) % 60);

                const expiryDate = new Date(expiryTime);
                const formattedDate = expiryDate.toLocaleDateString('en-GB');  // dd/mm/yyyy
                const formattedTime = expiryDate.toLocaleTimeString('en-GB');  // hh:mm:ss

                // ✅ Display in `dd/mm/yyyy hh:mm:ss` format with live countdown
                timer.innerHTML = `${formattedDate} ${formattedTime} 
                (${hours} hrs : ${minutes} mins : ${seconds} secs left)`;
            }

            // ✅ Update timer every second
            updateTimer();
            setInterval(updateTimer, 1000);
        });
    }

    // ✅ Handle form submission
    requestForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const foodItem = document.getElementById("foodItem").value.trim();
        const quantity = document.getElementById("quantity").value.trim();
        const location = document.getElementById("location").value.trim();
        const expiryTime = document.getElementById("expiryTime").value.trim();
        const description = document.getElementById("description").value.trim();

        if (foodItem && quantity && location && expiryTime) {
            const newRequest = {
                foodItem,
                quantity,
                location,
                expiryTime,
                description
            };
            foodRequests.push(newRequest);
            displayRequests();  // Refresh list
            requestForm.reset();
        } else {
            alert("Please fill in all required fields.");
        }
    });

    // ✅ Filter requests by location
    applyFilterBtn.addEventListener("click", function () {
        const filterValue = locationFilter.value.trim().toLowerCase();
        const filteredRequests = foodRequests.filter(request =>
            request.location.toLowerCase().includes(filterValue)
        );
        displayRequests(filteredRequests);
    });

    // ✅ Automatically remove expired requests every minute
    function removeExpiredRequests() {
        const currentTime = new Date().getTime();
        foodRequests = foodRequests.filter(request => new Date(request.expiryTime).getTime() > currentTime);
        displayRequests();
    }

    // ✅ Check and remove expired requests every minute
    setInterval(removeExpiredRequests, 60000);

    // ✅ Initial load: display all requests
    displayRequests();
});
