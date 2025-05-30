document.addEventListener("DOMContentLoaded", () => {
  Promise.all([
    fetch("/api/my_requests").then(res => res.json()),
    fetch("/api/status").then(res => res.json())
  ])
  .then(([requests, statuses]) => {
    const container = document.getElementById("recipient-requests-body");
    container.innerHTML = "";

    // Map of rid → status
    const statusMap = {};
    statuses.forEach(entry => {
      statusMap[entry.rid] = entry.status;
    });

    if (Array.isArray(requests) && requests.length > 0) {
      requests.forEach(item => {
        const card = document.createElement("div");
        card.classList.add("card");

        const status = statusMap[item.id] || "Donation Request Listed";
        let statusClass = "";
if (status === "Donation Request Listed") {
  statusClass = "blue-status";
} else if (status === "Acknowledgement Pending") {
  statusClass = "yellow-status";
} else if (status === "Donation Ongoing") {
  statusClass = "green-status";
}


        card.innerHTML = `
          <h3>${item.food_item.toUpperCase()}</h3>
          <p><strong>Quantity (in numbers):</strong> <span class="editable" data-field="quantity">${item.quantity}</span></p>
          <p><strong>Location:</strong> <span class="editable" data-field="location">${item.location}</span></p>
          <p><strong>Expiry:</strong> <span class = "expiry-time" data-field="expiry_time">${item.expiry_time}</span></p>
          <p><strong>Description:</strong> <span class="editable" data-field="desc">${item.desc || "No description provided."}</span></p>
          <p><strong>Status:</strong> <span class="donation-status ${statusClass}" >${status}</span></p>
        `;

        const editBtn = document.createElement("button");
        editBtn.textContent = "Edit";
        editBtn.classList.add("edit-btn");

        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remove";
        removeBtn.classList.add("remove-btn");

        card.appendChild(editBtn);
        card.appendChild(removeBtn);

        // Acknowledge button (for recipient to mark Ongoing)
        if (status === "Acknowledgement Pending") {
          const acknowledgeBtn = document.createElement("button");  
          acknowledgeBtn.textContent = "Acknowledge Donation";
          acknowledgeBtn.classList.add("acknowledge-btn");
      
          acknowledgeBtn.addEventListener("click", () => {
              // Send the request to acknowledge the donation
              fetch(`/api/acknowledge_donation/${item.id}`, {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
              })
              .then(res => res.json())
              .then(data => {
                  if (data.message === "Acknowledged successfully") {
                      acknowledgeBtn.remove();
                      card.querySelector(".donation-status").textContent = "Ongoing";
                      alert("Donation Acknowledged Successfully!")
                      location.reload();
                  } else {
                      alert(data.error || "Failed to acknowledge donation.");
                  }
              })
              .catch(err => alert("Error: " + err));
          });
      
          card.appendChild(acknowledgeBtn);
      }
      

        // Disable editing/removing if status is beyond initial listing
        if (status !== "Donation Request Listed" && status !="Acknowledgement Pending") {
          const markcomplete = document.createElement("button");
          markcomplete.textContent = "Mark as Completed";
          markcomplete.classList.add("acknowledge-btn");
      
          markcomplete.addEventListener("click", () => {
              fetch(`/api/markcomplete/${item.id}`, {   // Notice here: PATCH URL corrected
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
              })
              .then(res => res.json())
              .then(data => {
                  if (data.success) {
                      // ✅ Successfully marked complete
      
                      // Option 1: Reload the page to refresh everything
                      location.reload();
      
                      // OR Option 2 (better experience): Just remove this card
                      // card.remove();
                  } else {
                      // ❌ Some error occurred
                      alert(data.error || "Something went wrong!");
                  }
              })
              .catch(error => {
                  console.error("Error marking as completed:", error);
                  alert("Something went wrong!");
              });
          });
      
          card.appendChild(markcomplete);
      }

      if (status !== "Donation Request Listed") {
        editBtn.style.display = "none";
        removeBtn.style.display = "none";
      }
      
      card.appendChild(editBtn);
      card.appendChild(removeBtn);

      container.appendChild(card);

        // REMOVE handler
        removeBtn.addEventListener("click", () => {
          fetch(`/api/delete_request/${item.id}`, {
            method: "DELETE"
          })
          .then(res => {
            if (res.ok) {
              card.remove(); // Remove from UI
            } else {
              alert("Error deleting request");
            }
          });
        });

        // EDIT handler
        editBtn.addEventListener("click", () => {
          const editableFields = card.querySelectorAll(".editable");
          const updatedData = {};

          editableFields.forEach(span => {
            const newValue = prompt(`Edit ${span.dataset.field}`, span.textContent);
            if (newValue !== null) {
              span.textContent = newValue;
              updatedData[span.dataset.field] = newValue;
            }
          });

          fetch(`/api/edit_request/${item.id}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(updatedData)
          })
          .then(res => {
            if (!res.ok) alert("Failed to update");
          });
        });
      });
    } else {
      container.innerHTML = "<p>No requests found.</p>";
    }
  })
  .catch(error => console.error("Error fetching requests or statuses:", error));
});
