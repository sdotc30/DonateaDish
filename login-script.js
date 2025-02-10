let currentRole = 'donor'; // Default role

function switchRole(role) {
    const slider = document.querySelector('.slider');
    const buttons = document.querySelectorAll('.switcher button');
    
    if (role === 'donor') {
        slider.style.transform = 'translateX(0)';
        buttons[0].classList.add('active');
        buttons[1].classList.remove('active');
        currentRole = 'donor';
    } else {
        slider.style.transform = 'translateX(100%)';
        buttons[1].classList.add('active');
        buttons[0].classList.remove('active');
        currentRole = 'recipient';
    }

    document.getElementById('role-sign-in').textContent = capitalizeFirstLetter(currentRole);
    document.getElementById('role-sign-up').textContent = capitalizeFirstLetter(currentRole);
    document.getElementById('slider-role').textContent = capitalizeFirstLetter(currentRole);
}

function switchForm(formType) {
    const signInForm = document.getElementById('sign-in-form');
    const signUpForm = document.getElementById('sign-up-form');
    const signInButton = document.querySelector('.sign-in');
    const signUpButton = document.querySelector('.sign-up');

    if (formType === 'sign-in') {
        signInForm.classList.add('active');
        signUpForm.classList.remove('active');
        signInButton.style.background = '#ff6f61';
        signUpButton.style.background = '#ff6f61';
    } else {
        signUpForm.classList.add('active');
        signInForm.classList.remove('active');
        signUpButton.style.background = '#ff6f61';
        signInButton.style.background = '#ff6f61';
    }
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

document.addEventListener('DOMContentLoaded', () => {
    switchRole('donor');
});