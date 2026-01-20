const blogPosts = [
  {
    title: 'Design-first web dev: small things that feel nice',
    date: 'Jan 12, 2025',
    tags: ['builds', 'design'],
    description: 'A few tiny UI flourishes that make side projects feel polished without over-engineering.',
    url: '#',
    image: 'https://upload.wikimedia.org/wikipedia/en/6/6d/David_Bowie_-_Aladdin_Sane.jpeg'
  },
  {
    title: 'What I learned shipping three tools in 30 days',
    date: 'Dec 2, 2024',
    tags: ['learning', 'builds'],
    description: 'Lessons from a personal shipping sprint—scope, storytelling, and celebrating tiny wins.',
    url: '#',
    image: 'https://i.imgur.com/qA1M0Gu.jpg'
  },
  {
    title: 'On curiosity as a compass',
    date: 'Oct 18, 2024',
    tags: ['learning'],
    description: 'Using curiosity as a north star for projects, writing, and how I pick what to explore next.',
    url: '#'
  },
  {
    title: 'Weekend experiment: color palettes from songs',
    date: 'Aug 5, 2024',
    tags: ['fun', 'builds'],
    description: 'Mapping audio frequencies to color ramps to create playful palettes for cover art.',
    url: '#'
  }
];

const blogGrid = document.getElementById('blog-grid');
const filterButtons = document.querySelectorAll('.filter-button');
const themeToggle = document.getElementById('theme-toggle');
const form = document.getElementById('contact-form');
const formNote = document.getElementById('form-note');

function renderPosts(filter = 'all') {
  blogGrid.innerHTML = '';

  blogPosts
    .filter((post) => filter === 'all' || post.tags.includes(filter))
    .forEach((post) => {
      const card = document.createElement('article');
      card.className = 'blog-card';
      card.innerHTML = `
        ${post.image ? `<img class="blog-image" src="${post.image}" alt="${post.title} image" loading="lazy" />` : ''}
        <div class="blog-meta">
          <span>${post.date}</span>
          ${post.tags.map((tag) => `<span class="tag">${tag}</span>`).join('')}
        </div>
        <h3>${post.title}</h3>
        <p class="body">${post.description}</p>
        <a href="${post.url}" class="button ghost">Read on</a>
      `;
      blogGrid.appendChild(card);
    });
}

renderPosts();

filterButtons.forEach((button) => {
  button.addEventListener('click', () => {
    filterButtons.forEach((btn) => btn.classList.remove('active'));
    button.classList.add('active');
    renderPosts(button.dataset.filter);
  });
});

function setTheme(theme) {
  document.documentElement.classList.toggle('light', theme === 'light');
  localStorage.setItem('wildcat-theme', theme);
  themeToggle.querySelector('.icon').textContent = theme === 'light' ? '☀️' : '🌙';
}

const savedTheme = localStorage.getItem('wildcat-theme');
setTheme(savedTheme || 'dark');

themeToggle.addEventListener('click', () => {
  const next = document.documentElement.classList.contains('light') ? 'dark' : 'light';
  setTheme(next);
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const name = data.get('name');
  const email = data.get('email');

  formNote.textContent = `Thanks ${name}! I will reach out to ${email} soon.`;
  form.reset();
});
