const apiBase = (document.querySelector('meta[name="edugenie-api-base"]')?.content || "").replace(/\/$/, "");
const apiUrl = (path) => `${apiBase}${path}`;
const tabs = [...document.querySelectorAll(".tool-tab")];
const panels = [...document.querySelectorAll(".tool-panel")];

function activateTool(tool) {
  tabs.forEach((tab) => {
    const active = tab.dataset.tool === tool;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  panels.forEach((panel) => {
    const active = panel.dataset.panel === tool;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => activateTool(tab.dataset.tool));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    event.preventDefault();
    const direction = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1;
    const next = tabs[(index + direction + tabs.length) % tabs.length];
    activateTool(next.dataset.tool);
    next.focus();
  });
});

function payloadFromForm(form) {
  const payload = {};
  new FormData(form).forEach((value, key) => {
    const field = form.elements.namedItem(key);
    payload[key] = field?.dataset.type === "number" ? Number(value) : value;
  });
  return payload;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderText(result, data, key) {
  result.replaceChildren(element("p", "", data[key]));
}

function renderAnswer(result, data) {
  const answer = element("p", "answer-text", data.answer);
  const details = element("details", "answer-reasoning");
  const summary = element("summary", "", "Why this answer?");
  const reasoning = element("p", "", data.reasoning);
  details.append(summary, reasoning);
  result.replaceChildren(answer, details);
}

function renderQuiz(result, data) {
  const heading = element("h4", "", "Your practice quiz");
  result.replaceChildren(heading);
  data.questions.forEach((question, index) => {
    const card = element("article", "quiz-card");
    const title = element("h4");
    title.append(element("span", "quiz-index", String(index + 1).padStart(2, "0")));
    title.append(document.createTextNode(question.question));
    const options = element("div", "options");
    const feedback = element("p", "feedback");
    feedback.hidden = true;

    question.options.forEach((option) => {
      const button = element("button", "option", option);
      button.type = "button";
      button.addEventListener("click", () => {
        [...options.children].forEach((item) => {
          item.disabled = true;
          if (item.textContent === question.answer) item.classList.add("correct");
        });
        if (option !== question.answer) button.classList.add("incorrect");
        feedback.textContent = `${option === question.answer ? "Correct." : `Not quite—the answer is ${question.answer}.`} ${question.explanation}`;
        feedback.hidden = false;
      });
      options.append(button);
    });
    card.append(title, options, feedback);
    result.append(card);
  });
}

function renderPath(result, data) {
  result.replaceChildren(
    element("h4", "", `${data.topic}: your ${data.level} path`),
    element("p", "path-overview", data.overview),
  );
  data.stages.forEach((stage, index) => {
    const card = element("article", "stage-card");
    const body = element("div");
    body.append(element("h4", "", stage.title), element("p", "", stage.objective));
    const topics = element("ul");
    stage.topics.forEach((topic) => topics.append(element("li", "", topic)));
    body.append(topics);
    if (stage.activities.length) {
      body.append(element("p", "", `Try: ${stage.activities.join(" · ")}`));
    }
    card.append(element("span", "stage-badge", String(index + 1)), body);
    result.append(card);
  });
  if (data.resources.length) {
    result.append(element("h4", "", "Resource ideas"));
    const resources = element("div", "resource-list");
    data.resources.forEach((resource) => resources.append(element("span", "resource-pill", `${resource.type}: ${resource.suggestion}`)));
    result.append(resources);
  }
}

function errorMessage(data, status) {
  if (data?.error?.message) return data.error.message;
  if (status === 422) return "Please check the information you entered.";
  return "Something went wrong. Please try again.";
}

document.querySelectorAll(".tool-panel form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    const result = form.parentElement.querySelector(".result");
    const submit = form.querySelector("button[type='submit']");
    const originalLabel = submit.textContent;
    result.hidden = false;
    result.className = `result ${form.dataset.renderer === "quiz" ? "quiz-result" : form.dataset.renderer === "path" ? "path-result" : ""} loading`;
    result.replaceChildren(element("p", "", "EduGenie is thinking…"));
    submit.disabled = true;
    submit.textContent = "Working…";

    try {
      const response = await fetch(apiUrl(form.dataset.endpoint), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payloadFromForm(form)),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(errorMessage(data, response.status));

      result.classList.remove("loading", "error");
      if (form.dataset.renderer === "qa") renderAnswer(result, data);
      else if (form.dataset.renderer === "quiz") renderQuiz(result, data);
      else if (form.dataset.renderer === "path") renderPath(result, data);
      else renderText(result, data, form.dataset.resultKey);
      result.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
      result.classList.remove("loading");
      result.classList.add("error");
      result.replaceChildren(element("p", "", error.message));
    } finally {
      submit.disabled = false;
      submit.textContent = originalLabel;
    }
  });
});

async function checkHealth() {
  const status = document.querySelector("#api-status");
  try {
    const response = await fetch(apiUrl("/api/v1/health"));
    if (!response.ok) throw new Error();
    const data = await response.json();
    status.classList.add("online");
    status.lastChild.textContent = data.gemini_configured ? " API ready" : " Key needed";
  } catch {
    status.lastChild.textContent = " API offline";
  }
}

checkHealth();
