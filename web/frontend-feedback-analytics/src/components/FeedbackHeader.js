export function createHeader() {
  const header = document.createElement('nav');
  header.className = 'navbar navbar-expand-lg navbar-light bg-light';
  header.innerHTML = `
    <a class="navbar-brand" href="#">Feedback System</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ml-auto">
        <li class="nav-item">
          <a class="nav-link" href="view.html">View Feedback</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/trulens.html">Trulens Dashboard</a>
        </li>
      </ul>
    </div>
  `;
  return header;
}
