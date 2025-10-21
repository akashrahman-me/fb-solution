// Auto collection
const KEY = "ivasms";
if (confirm("Are you sure to clear memory?")) {
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
            result.push(`${number}:${otpMatch}`);
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

// Reveal collection
(() => {
    let sms = localStorage.getItem(KEY) || "[]";
    sms = JSON.parse(sms);

    const output = sms.join("\n");
    console.log(output);
    copy(output);
})();

// Auto add number
(async () => {
    const searchCountry = "KYRGYZSTAN";
    const searchSid = "FACEBOOK";
    const result = [];

    async function waitUntilVanish(selector, interval = 300) {
        while (document.querySelector(selector)) {
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

            if (
                country?.toLowerCase()?.includes(searchCountry.toLowerCase()) &&
                sid?.toLowerCase()?.includes(searchSid.toLowerCase()) &&
                !result.includes(country)
            ) {
                const body = document.getElementById("LiveTestSMS");
                body.id = "LiveTestSMSBlocked";
                anchor.click();
                await delay(1000);

                const addNumber = document.querySelector("button.btn.btn-primary.btn-block");
                addNumber?.click();

                result.push(country);

                await waitUntilVanish("#staticBackdropLabel");

                console.log(`Added ${country?.toUpperCase()}`);

                document.getElementById("LiveTestSMSBlocked").id = "LiveTestSMS";
            }
        }

        await new Promise((r) => setTimeout(r, 500));
    }
})();
