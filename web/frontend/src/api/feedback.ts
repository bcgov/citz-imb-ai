import type { userFeedbackType } from "@/types";

// Function to send user feedback to the server
const sendFeedback = async (
	feedbackType: userFeedbackType,
	recordingHash: string,
	comment?: string,
	trulensId?: string,
): Promise<string> => {
	const formData = new FormData();
	formData.append("feedback", feedbackType);
	formData.append("recording_id", recordingHash);
	formData.append("trulens_id", trulensId || ""); // Use empty string if trulensId is undefined
	if (comment) {
		formData.append("comment", comment);
	}

	// Send a POST request to the feedback endpoint
	const response = await fetch("/api/feedbackrag/", {
		method: "POST",
		headers: {
			Authorization: `Bearer ${localStorage.getItem("keycloak-token")}`,
		},
		body: formData,
	});

	// Throw an error if the response is not successful
	if (!response.ok) {
		throw new Error("Failed to send feedback");
	}

	// Parse and return the response data
	const data = await response.json();

	return data.message;
};

export default sendFeedback;
