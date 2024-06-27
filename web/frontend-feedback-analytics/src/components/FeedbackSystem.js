import "bootstrap";

let recording_id = null;

export function createFeedbackSystem() {
  const feedbackSystem = document.createElement("div");
  feedbackSystem.className = "m-5 feedback-system-search";
  feedbackSystem.innerHTML = `
    <h1>Feedback System</h1>
    <small class="text-muted">
      This is a feedback system for the legal information retrieval system. Enter a query in the input box below and
      submit it. The system will return a list of responses. For each response, you can provide feedback by selecting
      either "Thumbs Up" or "Thumbs Down". You can also provide feedback for multiple responses and submit them all at
      once using the "Submit Bulk Feedback" button. If you want to clear the responses, you can use the "Clear
      Responses" button.
    </small>
    <div class="form-group mt-2 mb-1">
      <input type="input" class="form-control" id="prompt" placeholder="Enter a query" />
      <div class="mt-1 mb-1">
        <button id="submit-question" class="mt-1 btn btn-dark">Submit</button>
      </div>
      <small id="promptHelp" class="form-text text-muted">Try to enter as many similar prompts. For example:</small>
<p>
  <button class="btn btn-outline-primary mt-2 btn-sm" type="button" data-bs-toggle="collapse" data-bs-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">
    View Example prompts
  </button>
</p>
<div class="collapse" id="collapseExample">
      <small id="promptHelpEx" class="form-text text-muted">
        <ul>
          <li>What regulations govern living in a condominium or apartment complex?</li>
          <!-- Add more example prompts if needed -->
          <li>What regulations govern living in a condominium or apartment complex?</li>
          <li>As a homeowner in a homeowners association (HOA), what rules am I subject to?</li>
          <li>What are the legal requirements for residents in a cooperative housing society?</li>
          <li>Are there specific laws that apply to residents in a gated community?</li>
          <li>What legislation oversees property owners in a planned unit development (PUD)?</li>
          <li>As a tenant in a rental property, what laws protect my rights?</li>
          <li>What are the legal obligations of property owners in a homeowners association (HOA)?</li>
          <li>What laws govern the management and operations of a residential strata corporation?</li>
          <li>Are there specific regulations for strata managers in my jurisdiction?</li>
          <li>What are the rights and responsibilities of owners in a strata-titled property?</li>
          <li>How are disputes between strata owners typically resolved under the law?</li>
          <li>What are the legal requirements for holding annual general meetings in a strata complex?</li>
          <li>Are there laws governing the maintenance and repair of common areas in a strata property?</li>
          <li>What is the role of the strata council in enforcing strata bylaws?</li>
          <li>What legislation governs the collection of strata fees and special levies?</li>
          <li>Are there regulations regarding the insurance requirements for strata properties?</li>
          <li>What laws protect strata owners from unfair practices by the strata corporation?</li>
          <li>Are there legal guidelines for the creation and amendment of strata bylaws?</li>
          <li>What are the legal implications of non-compliance with strata bylaws?</li>
          <li>How does the strata property act or equivalent legislation apply to mixed-use strata developments?</li>
        </ul>
        </small>
</div>
    <div id="responses"></div>
    <button id="SubmitBulk" class="mt-2 btn btn-dark d-none">Submit Bulk Feedback</button>
    <button id="clearResponses" class="mt-2 btn btn-danger d-none">Clear Responses</button>
  `;

  document.addEventListener("DOMContentLoaded", function () {
    document
      .getElementById("submit-question")
      .addEventListener("click", submitQuestion);
    document
      .getElementById("SubmitBulk")
      .addEventListener("click", submitBulkFeedback);
    document
      .getElementById("clearResponses")
      .addEventListener("click", clearResponses);
  });

  return feedbackSystem;
}

async function submitQuestion(event) {
  event.preventDefault();
  event.stopPropagation();
  const prompt = document.getElementById("prompt").value;

  const response = await fetch("/api/submit/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: `Bearer ${localStorage.getItem("keycloak-token")}`,
    },
    body: `prompt=${encodeURIComponent(prompt)}`,
  });

  const data = await response.json();
  const responses = data.responses;
  console.log(responses);
  recording_id = data.recording;

  const responsesDiv = document.getElementById("responses");
  responsesDiv.innerHTML = "";

  if (responses.length > 1) {
    document.getElementById("SubmitBulk").classList.remove("d-none");
    document.getElementById("clearResponses").classList.remove("d-none");
  }

  responses.forEach((response, index) => {
    const responseDiv = document.createElement("div");
    responseDiv.innerHTML = `
      <div class="card" style="margin:15px 15px;" id="card-${index}">
        <div class="card-body">
          <p><b>Response ${index + 1}</b></p>
          <b>Act Name:</b> <h5>${response["node.ActId"]}</h5>
          <b>Section Name:</b> <h5>${response["node.sectionName"]}</h5>
          <b>Section ID:</b><h5>${response["node.sectionId"]}</h5>
          <b>Regulation ID:</b><h5>${response["Regulations"]}</h5>
          <b>url:</b><h5>${response["node.url"]}</h5>
          <p>${response.text}</p>
          <div class="d-flex justify-content-center align-items-center">
            <div class="form-check form-check-inline">
                <input type="radio" name="feedback${index}" class="form-check-input" value="thumbs_up"> Thumbs Up
            </div>
            <div class="form-check form-check-inline">
                <input type="radio" name="feedback${index}" class="form-check-input" value="thumbs_down"> Thumbs Down
            </div>
                <button onclick="submitFeedback(${index}, '${recording_id}')" class="btn btn-outline-info">Submit Feedback</button>
            </div>
        </div>
      </div>    
    `;
    responsesDiv.appendChild(responseDiv);
  });
}

async function submitFeedback(index, recording_id) {
  const feedback = document.querySelector(
    `input[name="feedback${index}"]:checked`
  ).value;
  if (!recording_id) {
    alert("Please submit a question first");
    return;
  }

  const form = new FormData();
  form.append("feedback", feedback);
  form.append("index", index);
  form.append("recording_id", recording_id);

  const response = await fetch("/api/feedback/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("keycloak-token")}`,
    },
    body: form,
  });

  const data = await response.json();
  console.log(data);
}

async function submitBulkFeedback() {
  const responses = document.getElementById("responses").children;
  const feedback_values = [];

  for (let i = 0; i < responses.length; i++) {
    const feedback = document.querySelector(
      `input[name="feedback${i}"]:checked`
    );
    if (!feedback) {
      alert(
        `Please provide feedback for all responses. Response ${
          i + 1
        } is missing feedback.`
      );
      return;
    }
    feedback_values.push(feedback.value);
  }

  const form = new FormData();
  form.append("feedback", feedback_values);
  form.append("index", null); // null for bulk feedback
  form.append("recording_id", recording_id);
  form.append("bulk", true);

  const response = await fetch("/api/feedback/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("keycloak-token")}`,
    },
    body: form,
  });

  if (response.status === 200 || response.status === 201) {
    const data = await response.json();
    console.log(data);
    if (data.status === true) {
      alert("Feedback submitted successfully");
      clearResponses();
      document.getElementById("prompt").value = "";
      return;
    }
  }
  alert("Error submitting feedback");
}

function clearResponses() {
  document.getElementById("responses").innerHTML = "";
  document.getElementById("SubmitBulk").classList.add("d-none");
  document.getElementById("clearResponses").classList.add("d-none");
  recording_id = null;
}
