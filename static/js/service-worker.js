// SERVICE WORKER MY KANTY PWA
// Créez ce fichier dans : static/js/service-worker.js

const CACHE_NAME = 'mykanty-v1';
const OFFLINE_URL = '/offline/';

// Fichiers à mettre en cache pour fonctionnement hors ligne
const STATIC_CACHE_URLS = [
  '/',
  '/products/',
  '/services/',
  '/static/css/mobile-fix.css',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  OFFLINE_URL
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installation...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Mise en cache des fichiers statiques');
      return cache.addAll(STATIC_CACHE_URLS);
    })
  );
  
  self.skipWaiting();
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activation...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Suppression ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  self.clients.claim();
});

// Stratégie de cache : Network First, fallback sur Cache
self.addEventListener('fetch', (event) => {
  // Ignorer les requêtes non-GET
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Ignorer les requêtes vers des domaines externes (sauf Cloudinary pour les images)
  const url = new URL(event.request.url);
  if (url.origin !== location.origin && !url.hostname.includes('cloudinary.com')) {
    return;
  }
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Si la réponse est OK, la mettre en cache
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Si pas de réseau, utiliser le cache
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // Si pas en cache, afficher la page hors ligne
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
        });
      })
  );
});

// Notifications Push (optionnel)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'Nouvelle notification My Kanty',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Voir',
        icon: '/static/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Fermer',
        icon: '/static/icons/icon-96x96.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('My Kanty', options)
  );
});

// Gestion des clics sur les notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('[Service Worker] Chargé et prêt');