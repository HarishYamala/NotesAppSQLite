function toggleTheme() {
    const html = document.documentElement;
    const btn = document.getElementById("themeBtn");

    if (html.getAttribute("data-bs-theme") === "dark") {
        html.setAttribute("data-bs-theme", "light");
        localStorage.setItem("theme", "light");
        btn.innerText = "🌙";
    } else {
        html.setAttribute("data-bs-theme", "dark");
        localStorage.setItem("theme", "dark");
        btn.innerText = "☀️";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-bs-theme", savedTheme);

    const btn = document.getElementById("themeBtn");
    btn.innerText = savedTheme === "dark" ? "☀️" : "🌙";
});

function filterNotes() {
    const input = document.getElementById("searchInput").value.toLowerCase();
    const cards = document.getElementsByClassName("note-card");

    for (let card of cards) {
        const title = card.querySelector(".note-title").innerText.toLowerCase();
        const content = card.querySelector(".note-content").innerText.toLowerCase();

        if (title.includes(input) || content.includes(input)) {
            card.style.display = "block";
        } else {
            card.style.display = "none";
        }
    }
}
