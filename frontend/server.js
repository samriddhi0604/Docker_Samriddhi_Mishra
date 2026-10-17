/*
 * Express frontend - Docker assignment
 * Author: Samriddhi Mishra
 *
 * Shows the course registration form (same idea as Flask assignment 2) and
 * sends every submission to the Flask backend.
 *   success -> redirect to /success ("Data submitted successfully")
 *   error   -> show the error on the same page, without redirecting
 */
const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;
// Inside Docker Compose the backend is reachable by its service name "backend"
const BACKEND_URL = (process.env.BACKEND_URL || "http://localhost:5000").replace(/\/$/, "");
const COURSES = ["DevOps", "Python", "Flask", "MongoDB", "Docker"];

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, "public")));

function renderForm(res, status, error, values) {
  res.status(status).render("index", { error, values: values || {}, courses: COURSES, backendUrl: BACKEND_URL });
}

app.get("/", (req, res) => renderForm(res, 200, null, {}));

app.post("/submit", async (req, res) => {
  const values = {
    name: (req.body.name || "").trim(),
    email: (req.body.email || "").trim(),
    course: (req.body.course || "").trim(),
    message: (req.body.message || "").trim(),
  };

  try {
    // Send the form data to the Flask backend as JSON
    const response = await fetch(`${BACKEND_URL}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
      signal: AbortSignal.timeout(10000),
    });
    const result = await response.json().catch(() => ({}));

    if (response.ok) {
      console.log(`Submission ${result.submission && result.submission.id} saved by backend (${result.storage})`);
      return res.redirect(303, "/success");
    }
    console.log(`Backend rejected submission: ${response.status} ${result.error}`);
    return renderForm(res, response.status, result.error || `Backend error (HTTP ${response.status})`, values);
  } catch (err) {
    const reason = err.cause && err.cause.code ? err.cause.code : err.message;
    console.log(`Could not reach backend at ${BACKEND_URL}: ${reason}`);
    return renderForm(res, 502, `Could not reach the backend service (${reason}). Please try again.`, values);
  }
});

app.get("/success", (req, res) => res.render("success"));

// Small status page that proves the frontend can talk to the backend
app.get("/health", async (req, res) => {
  try {
    const r = await fetch(`${BACKEND_URL}/health`, { signal: AbortSignal.timeout(5000) });
    res.json({ frontend: "ok", backend: await r.json(), backendUrl: BACKEND_URL });
  } catch (err) {
    res.status(502).json({ frontend: "ok", backend: "unreachable", backendUrl: BACKEND_URL, error: err.message });
  }
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Frontend running on http://0.0.0.0:${PORT} (backend: ${BACKEND_URL})`);
});
