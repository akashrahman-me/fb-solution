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
