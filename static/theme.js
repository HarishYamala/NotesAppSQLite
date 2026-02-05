/* =====================
   THEME TOGGLE
===================== */

function toggleTheme() {
    const html = document.documentElement;
    const btn = document.getElementById("themeBtn");

    const currentTheme = html.getAttribute("data-bs-theme");

    if (currentTheme === "dark") {
        html.setAttribute("data-bs-theme", "light");
        localStorage.setItem("theme", "light");
        btn.innerText = "🌙";
    } else {
        html.setAttribute("data-bs-theme", "dark");
        localStorage.setItem("theme", "dark");
        btn.innerText = "☀️";
    }
}

/* =====================
   LOAD SAVED THEME
===================== */

document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-bs-theme", savedTheme);

    const btn = document.getElementById("themeBtn");
    if (btn) {
        btn.innerText = savedTheme === "dark" ? "☀️" : "🌙";
    }
});

/* =====================
   NOTES SEARCH FILTER
===================== */

function filterNotes() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    const query = input.value.toLowerCase();
    const cards = document.getElementsByClassName("note-card");

    for (let card of cards) {
        const title = card.querySelector(".note-title")?.innerText.toLowerCase() || "";
        const content = card.querySelector(".note-content")?.innerText.toLowerCase() || "";

        if (title.includes(query) || content.includes(query)) {
            card.style.display = "";
        } else {
            card.style.display = "none";
        }
    }
}

