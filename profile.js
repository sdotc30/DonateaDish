document.addEventListener("DOMContentLoaded", () => {

    // ✅ Simulated user data (Replace with Firebase data later)
    const userData = {
      name: "John Doe",
      email: "john.doe@example.com",
      role: "Donor",
      donations: [
        { item: "Rice", date: "2025-03-25", status: "Completed" },
        { item: "Bread", date: "2025-03-28", status: "Completed" }
      ],
      ongoingDonations: [
        { item: "Pasta", quantity: "5 servings", location: "Chennai" }
      ]
    };
  
    // ✅ Display User Info
    document.getElementById("user-name").textContent = userData.name;
    document.getElementById("user-email").textContent = userData.email;
    document.getElementById("user-role").textContent = userData.role;
  
    // ✅ Display Impact Summary
    document.getElementById("donations-count").textContent = userData.donations.length;
    document.getElementById("requests-fulfilled").textContent = Math.floor(userData.donations.length * 0.8);
  
    // ✅ Display Donation History
    const historyList = document.getElementById("history-list");
    historyList.innerHTML = "";  // Clear list
    if (userData.donations.length > 0) {
      userData.donations.forEach(donation => {
        const li = document.createElement("li");
        li.innerHTML = `
          <strong>${donation.item}</strong> - ${donation.date} 
          <span>(${donation.status})</span>
        `;
        historyList.appendChild(li);
      });
    } else {
      historyList.innerHTML = "<li>No past donations.</li>";
    }
  
    // ✅ Display Ongoing Donations
    const ongoingList = document.getElementById("ongoing-list");
    ongoingList.innerHTML = "";  // Clear list
    if (userData.ongoingDonations.length > 0) {
      userData.ongoingDonations.forEach(donation => {
        const li = document.createElement("li");
        li.innerHTML = `
          <strong>${donation.item}</strong> - ${donation.quantity} 
          <br>📍 ${donation.location}
        `;
        ongoingList.appendChild(li);
      });
    } else {
      ongoingList.innerHTML = "<li>No ongoing donations.</li>";
    }
  });
  