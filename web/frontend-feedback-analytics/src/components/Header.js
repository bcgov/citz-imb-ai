import bclogo from '../../assets/BC_logo.jpg'

export function createBootstrapHeader() {
  const nav = document.createElement('nav');
  nav.className = 'navbar navbar-expand-lg m-0 p-0';
  nav.innerHTML = `
    <div class="container-fluid">
          <a class="navbar-brand p-0 m-0" href="/index.html">
      <img src="${bclogo}" class="logo-header vanilla" alt="B.C logo" />
    </a>

      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
            <li class="nav-item m-2">
                <a class="btn btn-sm btn-outline-secondary" href="view.html">View Feedback</a>
            </li>
            <li class="nav-item m-2">
                <a class="btn btn-sm btn-outline-secondary" href="/trulens.html">Trulens Dashboard</a>
            </li>
        </ul>
      </div>
    </div>
  `;
  return nav;
}