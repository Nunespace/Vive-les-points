console.log("Hello World");
 
    
 
// Toggle mot de passe
  document.addEventListener("click", function(e) {
    if (e.target.closest(".toggle-password")) {
      const btn = e.target.closest(".toggle-password");
      const input = btn.previousElementSibling; // l'input est juste avant le bouton
      const icon = btn.querySelector("i");

      if (input.type === "password") {
        input.type = "text";
        icon.classList.replace("bi-eye", "bi-eye-slash");
      } else {
        input.type = "password";
        icon.classList.replace("bi-eye-slash", "bi-eye");
      }
    }
  });