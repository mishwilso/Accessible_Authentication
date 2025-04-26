const initPinScreen = (selector, onEnter) => {
	const container = document.querySelector(selector);
	const input = container.querySelector(".pin-value");
	const keys = container.querySelectorAll(".pin-keyboard-key");
	const status = document.getElementById("statusMsg");

	const clear = () => {
		input.value = "";
	};

	for (const key of keys) {
		key.addEventListener("click", () => {
			const value = key.textContent.trim();

			if (key.classList.contains("pin-keyboard-key--clear")) {
				clear();
				status.textContent = "";
			} else if (key.classList.contains("pin-keyboard-key--enter")) {
				if (input.value) {
					fetch("/submit_pin", {
						method: "POST",
						headers: {
							"Content-Type": "application/json"
						},
						body: JSON.stringify({
							pin: input.value,
							time_taken: getElapsedTime()
						})
					})
					.then(res => res.json())
					.then(data => {
						if (data.status === "confirm") {
							status.textContent = "PIN saved. Now confirm.";
							setTimeout(() => window.location.reload(), 500);
						} else if (data.status === "saved") {
							status.textContent = "PIN confirmed. Redirecting...";
							setTimeout(() => window.location.href = data.next, 500);
						} else if (data.status === "mismatch") {
							status.textContent = "PINs didn’t match. Try again.";
							setTimeout(() => window.location.reload(), 500);
						} else if (data.success === false) {
							status.textContent = data.error || "Incorrect PIN.";
							clear();
						} else if (data.success === true) {
							status.textContent = "Access granted ✅";
							setTimeout(() => window.location.href = data.next, 500);
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
