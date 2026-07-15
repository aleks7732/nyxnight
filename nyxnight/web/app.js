const form = document.getElementById('plan-form');
const submitButton = document.getElementById('submit-button');
const statusNode = document.getElementById('status');
const results = document.getElementById('results');
const stopsNode = document.getElementById('stops');
const transitNode = document.getElementById('transit-notes');
const caveatsNode = document.getElementById('caveats');

function setText(node, value) {
  node.textContent = String(value ?? '');
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.appendChild(document.createTextNode(String(text)));
  return node;
}

function listItems(target, values) {
  target.replaceChildren();
  values.forEach((value) => target.appendChild(element('li', '', value)));
}

function render(plan) {
  setText(document.getElementById('result-title'), plan.title);
  setText(document.getElementById('result-summary'), plan.summary);
  setText(document.getElementById('result-cost'), `$${plan.estimated_total_per_person.toFixed(2)} / person`);
  stopsNode.replaceChildren();
  plan.stops.forEach((stop, index) => {
    const article = element('article', 'stop');
    const schedule = element('div', 'stop-schedule');
    schedule.appendChild(element('p', 'stop-number', `${String(index + 1).padStart(2, '0')} / 03`));
    schedule.appendChild(element('p', 'time', `${stop.start_time} — ${stop.end_time}`));
    article.appendChild(schedule);

    const body = element('div', 'stop-body');
    body.appendChild(element('p', 'stop-category', `${stop.category} · live search handoff`));
    body.appendChild(element('h3', '', stop.name));
    body.appendChild(element('p', 'stop-reason', stop.reason));
    const verification = element('p', 'verification-note');
    verification.appendChild(element('strong', '', 'Check first. '));
    verification.appendChild(document.createTextNode(stop.verification_note));
    body.appendChild(verification);

    const action = element('a', 'stop-action', stop.action.label);
    action.href = stop.action.url;
    action.target = '_blank';
    action.rel = 'noopener noreferrer';
    action.setAttribute('aria-label', `${stop.action.label} for ${stop.name} (opens live search)`);
    action.appendChild(document.createTextNode(' ↗'));
    body.appendChild(action);
    article.appendChild(body);
    const budget = element('div', 'stop-budget');
    budget.appendChild(element('span', '', 'ALLOWANCE'));
    budget.appendChild(element('p', 'price', `$${stop.estimated_cost_per_person.toFixed(2)}`));
    article.appendChild(budget);
    stopsNode.appendChild(article);
  });
  listItems(transitNode, plan.transit_notes);
  listItems(caveatsNode, plan.caveats);
  results.hidden = false;
  results.focus({ preventScroll: true });
  results.scrollIntoView({ block: 'start' });
}

function payload() {
  const data = new FormData(form);
  return {
    city: data.get('city'),
    date: data.get('date'),
    party_size: Number(data.get('party_size')),
    budget_per_person: Number(data.get('budget_per_person')),
    vibe: data.get('vibe'),
    start_time: data.get('start_time'),
    end_time: data.get('end_time'),
  };
}

async function submit(event) {
  event.preventDefault();
  if (!form.reportValidity()) return;
  submitButton.disabled = true;
  setText(statusNode, 'Shaping the route…');
  try {
    const response = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload()),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail?.[0]?.msg || 'Planning failed.');
    render(body);
    setText(statusNode, 'Route ready. Use the Crail buttons to find current places.');
  } catch (error) {
    results.hidden = true;
    setText(statusNode, error instanceof Error ? error.message : 'Planning failed.');
  } finally {
    submitButton.disabled = false;
  }
}

const dateInput = form.elements.namedItem('date');
if (dateInput && !dateInput.value) {
  dateInput.value = new Date().toISOString().slice(0, 10);
}
form.addEventListener('submit', submit);
