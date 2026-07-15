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
  plan.stops.forEach((stop) => {
    const article = element('article', 'stop');
    article.appendChild(element('p', 'time', `${stop.start_time} — ${stop.end_time}`));
    const body = element('div');
    body.appendChild(element('h3', '', stop.name));
    body.appendChild(element('p', '', `${stop.category} · ${stop.reason}`));
    body.appendChild(element('p', '', stop.verification_note));
    article.appendChild(body);
    article.appendChild(element('p', 'price', `$${stop.estimated_cost_per_person.toFixed(2)}`));
    stopsNode.appendChild(article);
  });
  listItems(transitNode, plan.transit_notes);
  listItems(caveatsNode, plan.caveats);
  results.hidden = false;
  results.focus();
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
    setText(statusNode, 'Route ready. Verify real venues before leaving.');
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
