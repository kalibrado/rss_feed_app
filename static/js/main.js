
const form = document.getElementById('searchForm');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const stats = document.getElementById('stats');
const articlesContainer = document.getElementById('articlesContainer');
const articlesGrid = document.getElementById('articlesGrid');
const modal = document.getElementById('modal');
const submitBtn = document.getElementById('submitBtn');

let articlesData = [];
let startTime;

// Submit form
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const rssUrl = document.getElementById('rssUrl').value;
  const maxEntries = document.getElementById('maxEntries').value;
  const workers = document.getElementById('workers').value;

  await fetchFeed(rssUrl, maxEntries, workers);
});

// Fetch RSS feed
async function fetchFeed(url, maxEntries, workers) {
  // Reset
  hideAll();
  loading.classList.add('active');
  submitBtn.disabled = true;
  startTime = Date.now();

  try {
    const apiUrl = `/?url=${encodeURIComponent(url)}&max_entries=${maxEntries}&workers=${workers}`;

    const response = await fetch(apiUrl);

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    const xmlText = await response.text();
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, 'text/xml');

    // Parse articles
    articlesData = parseRSS(xmlDoc);

    if (articlesData.length === 0) {
      throw new Error('Aucun article trouvé dans le flux');
    }

    // Display results
    displayStats(articlesData);
    displayArticles(articlesData);

  } catch (err) {
    showError(err.message);
  } finally {
    loading.classList.remove('active');
    submitBtn.disabled = false;
  }
}

// Parse RSS XML
function parseRSS(xmlDoc) {
  const items = xmlDoc.querySelectorAll('item');
  const articles = [];

  items.forEach(item => {
    const article = {
      title: item.querySelector('title')?.textContent || 'Sans titre',
      link: item.querySelector('link')?.textContent || '#',
      content: item.querySelector('content\\:encoded, encoded')?.textContent ||
        item.querySelector('description')?.textContent || '',
      pubDate: item.querySelector('pubDate')?.textContent || '',
      image: null,
      tags: []
    };

    // Extract image from enclosure
    const enclosure = item.querySelector('enclosure');
    if (enclosure) {
      article.image = enclosure.getAttribute('url');
    }

    // Extract tags
    const categories = item.querySelectorAll('category');
    categories.forEach(cat => {
      const tag = cat.textContent.trim();
      if (tag) article.tags.push(tag);
    });

    articles.push(article);
  });

  return articles;
}

// Display stats
function displayStats(articles) {
  const endTime = Date.now();
  const duration = ((endTime - startTime) / 1000).toFixed(1);

  const withImages = articles.filter(a => a.image).length;
  const totalTags = articles.reduce((sum, a) => sum + a.tags.length, 0);

  document.getElementById('statTotal').textContent = articles.length;
  document.getElementById('statWithImages').textContent = withImages;
  document.getElementById('statTags').textContent = totalTags;
  document.getElementById('statTime').textContent = duration + 's';

  stats.classList.add('active');
}

// Display articles
function displayArticles(articles) {
  articlesGrid.innerHTML = '';

  articles.forEach((article, index) => {
    const card = createArticleCard(article, index);
    articlesGrid.appendChild(card);
  });

  articlesContainer.classList.add('active');
}

// Create article card
function createArticleCard(article, index) {
  const card = document.createElement('div');
  card.className = 'article-card';
  card.onclick = () => openModal(article);

  // Extract summary from content
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = article.content;
  const summary = tempDiv.textContent.substring(0, 150) + '...';

  // Format date
  const date = article.pubDate ? new Date(article.pubDate).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }) : '';

  card.innerHTML = `
                <div class="article-image">
                    ${article.image ?
      `<img src="${article.image}" alt="${article.title}" onerror="this.parentElement.innerHTML='📰'">` :
      '📰'
    }
                </div>
                <div class="article-content">
                    <div class="article-meta">
                        ${date ? `<span class="article-date">📅 ${date}</span>` : ''}
                    </div>
                    ${article.tags.length > 0 ? `
                        <div class="article-tags">
                            ${article.tags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                    <h3 class="article-title">${article.title}</h3>
                    <p class="article-summary">${summary}</p>
                    <span class="read-more">Lire l'article →</span>
                </div>
            `;

  return card;
}

// Open modal
function openModal(article) {
  document.getElementById('modalTitle').textContent = article.title;
  document.getElementById('modalContent').innerHTML = article.content;
  document.getElementById('modalLink').href = article.link;

  // Image
  const modalImage = document.getElementById('modalImage');
  if (article.image) {
    modalImage.src = article.image;
    modalImage.style.display = 'block';
  } else {
    modalImage.style.display = 'none';
  }

  // Meta
  const date = article.pubDate ? new Date(article.pubDate).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }) : '';

  document.getElementById('modalMeta').innerHTML = `
                ${date ? `<span class="article-date">📅 ${date}</span>` : ''}
                ${article.tags.length > 0 ? `
                    <div class="article-tags">
                        ${article.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            `;

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// Close modal
document.getElementById('modalClose').onclick = closeModal;
modal.onclick = (e) => {
  if (e.target === modal) closeModal();
};

function closeModal() {
  modal.classList.remove('active');
  document.body.style.overflow = 'auto';
}

// Keyboard shortcut
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

// Show error
function showError(message) {
  document.getElementById('errorMessage').textContent = message;
  error.classList.add('active');
}

// Hide all
function hideAll() {
  error.classList.remove('active');
  stats.classList.remove('active');
  articlesContainer.classList.remove('active');
}

// Example URLs
const examples = [
  'https://www.lesnumeriques.com/rss-news.xml',
  'https://korben.info/feed',
  'https://www.lemonde.fr/rss/une.xml'
];

// Add example button (optional)
if (examples.length > 0) {
  const exampleBtn = document.createElement('button');
  exampleBtn.type = 'button';
  exampleBtn.className = 'btn';
  exampleBtn.style.background = 'var(--secondary)';
  exampleBtn.style.color = 'white';
  exampleBtn.textContent = '💡 Exemple';
  exampleBtn.onclick = () => {
    document.getElementById('rssUrl').value = examples[0];
  };
  document.querySelector('.input-wrapper').appendChild(exampleBtn);
}