
const locations = [
    "Paris, France",
    "New York, USA",
    "Tokyo, Japan",
    "Rome, Italy",
    "London, UK",
    "Dubai, UAE",
    "Bali, Indonesia",
    "Barcelona, Spain"
];

const input = document.getElementById("locationInput");
const suggestionsBox = document.getElementById("suggestions");

input.addEventListener("input", () => {
    const value = input.value.toLowerCase();
    suggestionsBox.innerHTML = "";

    if (!value) {
        suggestionsBox.classList.add("d-none");
        return;
    }

    const matches = locations.filter(loc =>
        loc.toLowerCase().includes(value)
    );

    matches.forEach(loc => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "list-group-item list-group-item-action";
        item.textContent = loc;

        item.onclick = () => {
            input.value = loc;
            suggestionsBox.classList.add("d-none");
            loadGallery(loc);
        };

        suggestionsBox.appendChild(item);
    });

    suggestionsBox.classList.toggle("d-none", matches.length === 0);
});

document.addEventListener("click", (e) => {
    if (!e.target.closest("#locationInput")) {
        suggestionsBox.classList.add("d-none");
    }
});
function loadGallery(location) {
    const gallery = document.getElementById("gallery");
    gallery.innerHTML = "";

    const images = {
        "Paris, France": ["paris1.jpg", "paris2.jpg", "paris3.jpg"],
        "Tokyo, Japan": ["tokyo1.jpg", "tokyo2.jpg", "tokyo3.jpg"],
        "New York, USA": ["ny1.jpg", "ny2.jpg", "ny3.jpg"]
    };

    const items = images[location] || [];

    items.forEach((img, index) => {
        gallery.innerHTML += `
        <div class="col">
            <div class="card h-100 border-0 shadow-sm rounded-3 overflow-hidden">
                <div class="ratio ratio-4x3">
                    <img src="/static/img/${img}" class="card-img-top" style="object-fit:cover">
                </div>
                <div class="card-body p-3">
                    <h6 class="fw-bold mb-1">Experience ${index + 1}</h6>
                    <p class="text-muted small mb-0">Top activity in ${location}</p>
                </div>
            </div>
        </div>`;
    });
}
