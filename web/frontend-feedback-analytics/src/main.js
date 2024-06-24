import './style.scss'
import bclogo from '../assets/BC_logo.jpg'
import { setupCounter } from '../counter.js'

document.querySelector('#app').innerHTML = `
  <div>
    <a href="" target="_blank">
      <img src="${bclogo}" class="logo vanilla" alt="B.C logo" />
    </a>
    <h1>A.I Dashboard</h1>
    <button class="button" onclick="window.location.href = '/login.html'">Login</button>
  </div>
`

setupCounter(document.querySelector('#counter'))
