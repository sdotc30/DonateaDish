// ✅ Firebase Imports
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.3.0/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
} from "https://www.gstatic.com/firebasejs/11.3.0/firebase-auth.js";

// ✅ Firebase Configuration
const firebaseConfig = {
  apiKey: "AIzaSyCeqvhbvu0BQ5MursJbkk7ZE0rAw27Cl3I",
  authDomain: "leftover-food-donation--eeee.firebaseapp.com",
  projectId: "leftover-food-donation--eeee",
  storageBucket: "leftover-food-donation--eeee.appspot.com",
  messagingSenderId: "94435637421",
  appId: "1:94435637421:web:8a6f824ad863f595b3ee24",
};

// ✅ Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// ✅ Default Role
let currentRole = "donor";

// ✅ Capitalize First Letter
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

// ✅ Switch Role Logic (Donor <-> Recipient)
function switchRole(role) {

    console.log(`Switching to: ${role}`);
  const slider = document.querySelector(".slider");
  const buttons = document.querySelectorAll(".switcher button");

  if (role === "donor") {
    slider.style.transform = "translateX(0)";
    buttons[0].classList.add("active");
    buttons[1].classList.remove("active");
    currentRole = "donor";
  } else {
    slider.style.transform = "translateX(100%)";
    buttons[1].classList.add("active");
    buttons[0].classList.remove("active");
    currentRole = "recipient";
  }

  document.getElementById("role-sign-in").textContent = capitalizeFirstLetter(
    currentRole
  );
  document.getElementById("role-sign-up").textContent = capitalizeFirstLetter(
    currentRole
  );
  document.getElementById("slider-role").textContent = capitalizeFirstLetter(
    currentRole
  );
}

// ✅ Switch Between Sign-In and Sign-Up
function switchForm(formType) {
  const signInForm = document.getElementById("sign-in-form");
  const signUpForm = document.getElementById("sign-up-form");

  if (formType === "sign-in") {
    signInForm.classList.add("active");
    signUpForm.classList.remove("active");
  } else {
    signUpForm.classList.add("active");
    signInForm.classList.remove("active");
  }
}

// ✅ Handle User Sign-Up (Works for Donors & Recipients)
document
  .querySelector(".sign-up")
  .addEventListener("click", async (e) => {
    e.preventDefault();
    const email = document.getElementById("sign-up-email").value;
    const password = document.getElementById("sign-up-password").value;

    if (!email || !password) {
      alert("⚠️ Please enter both email and password.");
      return;
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      );
      alert("🎉 Signup Successful! Welcome, " + userCredential.user.email);

      // ✅ Redirect to Donor/Recipient Dashboard
      if (currentRole === "donor") {
        window.location.href = "donor_dashboard.html";
      } else {
        window.location.href = "recipient_dashboard.html";
      }
    } catch (error) {
      console.error("❌ Sign-Up Error:", error.message);
      alert("❌ Error: " + error.message);
    }
  });

// ✅ Handle User Sign-In (Works for Donors & Recipients)
document
  .querySelector(".sign-in")
  .addEventListener("click", async (e) => {
    e.preventDefault();
    const email = document.getElementById("sign-in-email").value;
    const password = document.getElementById("sign-in-password").value;

    if (!email || !password) {
      alert("⚠️ Please enter both email and password.");
      return;
    }

    try {
      const userCredential = await signInWithEmailAndPassword(
        auth,
        email,
        password
      );
      alert("✅ Login Successful! Welcome back, " + userCredential.user.email);

      // ✅ Redirect to Donor/Recipient Dashboard
      if (currentRole === "donor") {
        window.location.href = "donor_dashboard.html";
      } else {
        window.location.href = "recipient_dashboard.html";
      }
    } catch (error) {
      alert("❌ Error: " + error.message);
    }
  });

// ✅ Initialize with Default Role
document.addEventListener("DOMContentLoaded", () => {
  switchRole("donor");
});

// ✅ Ensure DOM is fully loaded before adding event listeners
document.addEventListener("DOMContentLoaded", () => {
    switchRole("donor"); // Set default role to donor
  
    // ✅ Add event listeners to switch buttons
    document.getElementById("btn-donor").addEventListener("click", () => {
      switchRole("donor");
    });
  
    document.getElementById("btn-recipient").addEventListener("click", () => {
      switchRole("recipient");
    });
  });
  
