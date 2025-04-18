const login=document.getElementById("login");
function toggleDropDown() {
        console.log('user icon clicked')
        const dropdown = document.getElementById('dropdown-menu');
        dropdown.classList.toggle('show');
}

// Close the dropdown if clicked outside
login.onclick = function(event) {
        console.log('Window clicked')
        const dropdown = document.getElementById('dropdown-menu');
        const icon = document.querySelector('.user-icon');
        if (dropdown && !icon.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.remove('show');
        }
       
 }

