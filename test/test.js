// Auto save OTPs
javascript: (() => {
    const KEY = "ivasms";
    if (localStorage.getItem(KEY) && JSON.parse(localStorage.getItem(KEY))?.length > 0 && confirm("Are you sure to clear memory?")) {
        localStorage.removeItem(KEY);
    }

    setInterval(() => {
        let sms = localStorage.getItem(KEY) || "[]";
        sms = JSON.parse(sms);

        const rows = document.querySelectorAll("#LiveTestSMS tr");
        const result = [];

        rows.forEach((row) => {
            const number = row.querySelector(".CopyText")?.innerText.trim();
            const msg = row.querySelector("td:last-child")?.innerText.trim();
            const otpMatch = msg?.replace(/\D+/g, "");

            if (number && otpMatch) {
                result.push(`${number}  ${otpMatch} ${result.length}`);
            }
        });

        result.forEach((item) => {
            if (!sms.includes(item)) {
                sms.push(item);
                console.log(item);
            }
        });
        localStorage.setItem(KEY, JSON.stringify(sms));
    }, 3000);
})();

// Auto Copy OTPs
javascript: (() => {
    const KEY = "ivasms";
    let sms = localStorage.getItem(KEY) || "[]";
    sms = JSON.parse(sms);
    console.log(`${sms.length} numbers`);
    copy(sms.join("\n"));
    setTimeout(() => {
        navigator.clipboard.writeText(sms.join("\n"));
    }, 1000);
})();

// Auto add numbers
javascript: (async () => {
    const storageSearchCountry = JSON.parse(localStorage.getItem("search_country") || "[]");
    const searchCountry = prompt("Country name", storageSearchCountry.join(",")).split(",");
    localStorage.setItem("search_country", JSON.stringify(searchCountry));

    const searchSid = "FACEBOOK";
    const result = [];

    async function waitUntilVanish(selector, interval = 300) {
        while (document.querySelector(selector)) {
            await new Promise((r) => setTimeout(r, interval));
        }
    }
    async function waitUntilVisible(selector, interval = 300) {
        while (!document.querySelector(selector)?.checkVisibility()) {
            await new Promise((r) => setTimeout(r, interval));
        }
    }

    function delay(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    while (true) {
        const rows = document.querySelectorAll("#LiveTestSMS tr");

        for (const row of rows) {
            const anchor = row.querySelector("td .text-dark.stretched-link");
            const country = anchor?.innerText.trim();
            const sid = row.querySelector("td .fw-semi-bold.ms-2")?.innerText.trim();

            const found = searchCountry.some((c) => country?.toLowerCase().includes(c?.toLowerCase()));

            if (found && sid?.toLowerCase()?.includes(searchSid?.toLowerCase()) && !result.includes(country)) {
                const body = document.getElementById("LiveTestSMS");
                body.id = "LiveTestSMSBlocked";
                anchor.click();
                await delay(3000);

                const addNumber = document.querySelector("button.btn.btn-primary.btn-block");
                addNumber?.click();

                await waitUntilVisible("img[src='https://www.ivasms.com/assets/img/icons/check-true.png']");

                result.push(country);
                console.log(`Added ${country?.toUpperCase()}`);

                document.querySelector("[data-dismiss='modal']").click();

                await delay(1000);
                document.getElementById("LiveTestSMSBlocked").id = "LiveTestSMS";
            }
        }

        await new Promise((r) => setTimeout(r, 500));
    }
})();

// Copy all numbers
javascript: (async () => {
    async function waitUntilExist(getElementFn, interval = 300) {
        let el;
        while (!(el = getElementFn())) {
            await new Promise((r) => setTimeout(r, interval));
        }
        return el;
    }

    const accordion = document.getElementById("accordion");
    const cards = [...accordion.querySelectorAll(".card")].reverse();

    for (const card of cards) {
        const anchor = card.querySelector('a[data-id][onclick*="GetNumber"]');
        anchor.click();
        await waitUntilExist(() => card.querySelector(".MyNumber tr"));
    }

    let allNumbers = [];
    [...document.querySelectorAll(".MyNumber")].forEach((body) => {
        const rangNumbers = [...body.querySelectorAll("tr")].map((tr) => tr.innerText.trim());
        allNumbers = [...new Set([...allNumbers, ...rangNumbers])];
    });

    navigator.clipboard.writeText(allNumbers.join("\n"));
})();

// Stop toggle
javascript: (() => {
    const liveTestSMS = document.getElementById("LiveTestSMS");
    const liveTestSMSBlocked = document.getElementById("LiveTestSMSBlocked");

    if (liveTestSMS) {
        liveTestSMS.id = "LiveTestSMSBlocked";
    } else if (liveTestSMSBlocked) {
        liveTestSMSBlocked.id = "LiveTestSMS";
    }
})();

// Country stats
javascript: (async () => {
    const searchSid = "FACEBOOK";
    const result = {};

    while (true) {
        const rows = document.querySelectorAll("#LiveTestSMS tr");

        for (const row of rows) {
            const anchor = row.querySelector("td .text-dark.stretched-link");
            const country = anchor?.innerText
                .trim()
                .toLowerCase()
                .replace(/[^a-zA-Z ]/g, "");
            const sid = row.querySelector("td .fw-semi-bold.ms-2")?.innerText.trim();

            if (sid?.toLowerCase()?.includes(searchSid?.toLowerCase())) {
                result[country] = (result[country] || 0) + 1;
                document.getElementById("countryBox")?.remove();

                const box = document.createElement("div");
                box.id = "countryBox";
                box.style.position = "fixed";
                box.style.bottom = "30px";
                box.style.right = "30px";
                box.style.padding = "20px 24px";
                box.style.borderRadius = "16px";
                box.style.background = "rgba(30, 30, 30, 0.15)";
                box.style.backdropFilter = "blur(4px)";
                box.style.boxShadow = "0 6px 20px rgba(0, 0, 0, 0.4)";
                box.style.color = "#000000";
                box.style.fontFamily = "'Inter', sans-serif";
                box.style.fontSize = "15px";
                box.style.zIndex = "999999";
                box.style.border = "1px solid rgba(255,255,255,0.15)";
                box.style.maxHeight = "300px";
                box.style.overflowY = "scroll";
                box.style.scrollbarWidth = "none";
                box.style.msOverflowStyle = "none";

                const style = document.createElement("style");
                style.innerHTML = "#countryBox::-webkit-scrollbar { display: none; }";
                document.head.appendChild(style);

                const title = document.createElement("div");
                title.innerHTML = "🌍 <b>Country Stats</b>";
                title.style.fontSize = "17px";
                title.style.textAlign = "center";
                title.style.marginBottom = "12px";
                title.style.borderBottom = "1px solid rgba(255,255,255,0.2)";
                title.style.paddingBottom = "6px";

                const sorted = Object.fromEntries(Object.entries(result).sort((a, b) => b[1] - a[1]));
                const list = document.createElement("div");
                Object.entries(sorted).forEach(([k, v]) => {
                    const row = document.createElement("div");
                    row.style.display = "flex";
                    row.style.justifyContent = "space-between";
                    row.style.padding = "4px 0";
                    row.style.borderBottom = "1px dashed rgba(255,255,255,0.1)";
                    row.innerHTML =
                        "<span style='text-transform: capitalize'>" +
                        k.trim() +
                        "</span><span style='font-weight:600;color:#000000'>" +
                        v +
                        "</span>";
                    list.appendChild(row);
                });

                box.appendChild(title);
                box.appendChild(list);
                document.body.appendChild(box);
            }
        }

        await new Promise((r) => setTimeout(r, 500));
    }
})();
