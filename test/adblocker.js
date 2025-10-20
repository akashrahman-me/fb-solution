document.addEventListener("click", function (e) {
    let link = e.target.closest("a");
    if (!link) return;

    // Prevent default navigation
    e.preventDefault();

    // Modify URL
    let url = link.href;
    url = url.replace(/\.com(?=[\/?#]|$)/, ".com.");

    // Navigate to modified URL
    window.location.href = url;
});
