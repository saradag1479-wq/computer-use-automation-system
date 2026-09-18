from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Member Back Office")

MEMBERS = {
    "M1001": {"name": "Jordan Lee", "status": "ACTIVE"},
    "M1002": {"name": "Taylor Morgan", "status": "RESTRICTED"},
}

PAGE = '''<!doctype html>
<html>
<head><title>Member Back Office</title></head>
<body>
<h1>Member Back Office</h1>
<p>Legacy Operations Portal</p>

<form id="lookup">
  <label for="member-id">Member ID</label>
  <input id="member-id" name="member-id">
  <button type="submit">Search Member</button>
</form>

<div id="result" role="status"></div>

<script>
const members = %s;
document.getElementById("lookup").addEventListener("submit", function(e) {
  e.preventDefault();
  const id = document.getElementById("member-id").value.trim();
  const result = document.getElementById("result");

  if (!id) {
    result.textContent = "Validation error: Member ID is required.";
    return;
  }

  if (!members[id]) {
    result.textContent = "Business outcome: Member not found.";
    return;
  }

  result.textContent =
    "Member Name: " + members[id].name +
    " | Account Status: " + members[id].status;
});
</script>
</body>
</html>''' % repr(MEMBERS)

@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
