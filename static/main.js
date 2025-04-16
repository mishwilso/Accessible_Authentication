// To be filled later
/***************************************************************************************
*    Title: <title of program/source code>
*    Author: <author(s) names>
*    Date: <date>
*    Code version: <code version>
*    Availability: <where it's located>
*
***************************************************************************************/
// =================== PIN LOCK ===================
const initPinScreen = (selector, onEnter) => {
	const container = document.querySelector(selector);
	const input = container.querySelector(".pin-value");
	const keys = container.querySelectorAll(".pin-keyboard-key");

	const clear = () => {
		input.value = "";
	};

	for (const key of keys) {
		key.addEventListener("click", () => {
			const value = key.textContent.trim();

			if (key.classList.contains("pin-keyboard-key--clear")) {
				clear();
			} else if (key.classList.contains("pin-keyboard-key--enter")) {
				if (input.value) {
					fetch("/submit_pin", {
						method: "POST",
						headers: {
							"Content-Type": "application/json"
						},
						body: JSON.stringify({ pin: input.value })
					})
					.then(res => res.json())
					.then(data => {
						if (data.success === false) {
							alert(data.error);
							clear();
						} else {
							window.location.href = data.next;
						}
					});
				}
			} else {
				input.value += value;
			}
		});
	}
};

initPinScreen("#mainPinScreen", (pin, clear) => {
	console.log(`Entered Pin: ${pin}`);
	clear();
});

// ============== PATTERN LOCK ===============

