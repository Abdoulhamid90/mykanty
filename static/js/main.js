// ==========================================
// MARKETPLACE - JavaScript Principal
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // GESTION DES ALERTES
    // ==========================================
    
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            });
        }
        
        // Auto-fermeture après 5 secondes
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
    
    
    // ==========================================
    // GESTION DU PANIER
    // ==========================================
    
    function updateCartCount() {
        const cartData = JSON.parse(localStorage.getItem('cart') || '[]');
        const totalItems = cartData.reduce((sum, item) => sum + item.quantity, 0);
        const cartBadge = document.getElementById('cart-count');
        if (cartBadge) {
            cartBadge.textContent = totalItems;
            cartBadge.style.display = totalItems > 0 ? 'block' : 'none';
        }
    }
    
    // Ajouter au panier
    window.addToCart = function(productId, productName, price, image) {
        let cart = JSON.parse(localStorage.getItem('cart') || '[]');
        
        // Vérifier si le produit existe déjà
        const existingItem = cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                id: productId,
                name: productName,
                price: price,
                image: image,
                quantity: 1
            });
        }
        
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCount();
        showNotification('Produit ajouté au panier !', 'success');
        
        // Envoyer au serveur si l'utilisateur est connecté
        if (document.body.dataset.userAuthenticated === 'true') {
            syncCartWithServer(cart);
        }
    };
    
    // Retirer du panier
    window.removeFromCart = function(productId) {
        let cart = JSON.parse(localStorage.getItem('cart') || '[]');
        cart = cart.filter(item => item.id !== productId);
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCount();
        
        if (document.body.dataset.userAuthenticated === 'true') {
            syncCartWithServer(cart);
        }
        
        // Recharger la page du panier si on y est
        if (window.location.pathname.includes('/cart')) {
            location.reload();
        }
    };
    
    // Mettre à jour la quantité
    window.updateQuantity = function(productId, quantity) {
        let cart = JSON.parse(localStorage.getItem('cart') || '[]');
        const item = cart.find(item => item.id === productId);
        
        if (item) {
            item.quantity = parseInt(quantity);
            if (item.quantity <= 0) {
                removeFromCart(productId);
                return;
            }
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartCount();
            
            if (document.body.dataset.userAuthenticated === 'true') {
                syncCartWithServer(cart);
            }
        }
    };
    
    // Synchroniser avec le serveur
    function syncCartWithServer(cart) {
        fetch('/api/cart/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ cart: cart })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Erreur de synchronisation du panier');
            }
        })
        .catch(error => console.error('Erreur:', error));
    }
    
    // Initialiser le compteur du panier
    updateCartCount();
    
    
    // ==========================================
    // NOTIFICATIONS
    // ==========================================
    
    window.showNotification = function(message, type = 'info') {
        const container = document.querySelector('.messages-container') || createMessagesContainer();
        
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <i class="fas fa-${iconMap[type]}"></i>
            ${message}
            <button class="alert-close">&times;</button>
        `;
        
        container.appendChild(alert);
        
        // Ajouter l'événement de fermeture
        const closeBtn = alert.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            alert.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => alert.remove(), 300);
        });
        
        // Auto-fermeture
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    };
    
    function createMessagesContainer() {
        const container = document.createElement('div');
        container.className = 'messages-container';
        document.body.appendChild(container);
        return container;
    }
    
    
    // ==========================================
    // MENU MOBILE
    // ==========================================
    
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', () => {
            navbarMenu.style.display = navbarMenu.style.display === 'block' ? 'none' : 'block';
        });
    }
    
    
    // ==========================================
    // RECHERCHE INSTANTANÉE
    // ==========================================
    
    const searchInput = document.querySelector('.search-input');
    let searchTimeout;
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            const query = this.value.trim();
            
            if (query.length >= 3) {
                searchTimeout = setTimeout(() => {
                    instantSearch(query);
                }, 500);
            }
        });
    }
    
    function instantSearch(query) {
        fetch(`/api/products/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Afficher les résultats de recherche instantanée
                console.log('Résultats de recherche:', data);
            })
            .catch(error => console.error('Erreur de recherche:', error));
    }
    
    
    // ==========================================
    // WISHLIST (LISTE DE SOUHAITS)
    // ==========================================
    
    window.toggleWishlist = function(productId) {
        let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
        
        const index = wishlist.indexOf(productId);
        
        if (index > -1) {
            wishlist.splice(index, 1);
            showNotification('Retiré de la liste de souhaits', 'info');
        } else {
            wishlist.push(productId);
            showNotification('Ajouté à la liste de souhaits', 'success');
        }
        
        localStorage.setItem('wishlist', JSON.stringify(wishlist));
        updateWishlistUI(productId);
    };
    
    function updateWishlistUI(productId) {
        const buttons = document.querySelectorAll(`[data-product-id="${productId}"]`);
        const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
        const isInWishlist = wishlist.includes(productId);
        
        buttons.forEach(button => {
            if (isInWishlist) {
                button.classList.add('in-wishlist');
                button.querySelector('i').classList.replace('far', 'fas');
            } else {
                button.classList.remove('in-wishlist');
                button.querySelector('i').classList.replace('fas', 'far');
            }
        });
    }
    
    
    // ==========================================
    // NOTES / ÉTOILES
    // ==========================================
    
    const starRatings = document.querySelectorAll('.star-rating');
    
    starRatings.forEach(rating => {
        const stars = rating.querySelectorAll('.star');
        const input = rating.querySelector('input[type="hidden"]');
        
        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const value = index + 1;
                if (input) input.value = value;
                
                stars.forEach((s, i) => {
                    if (i < value) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
            });
            
            star.addEventListener('mouseenter', () => {
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('hover');
                    } else {
                        s.classList.remove('hover');
                    }
                });
            });
        });
        
        rating.addEventListener('mouseleave', () => {
            stars.forEach(s => s.classList.remove('hover'));
        });
    });
    
    
    // ==========================================
    // HELPERS / UTILITAIRES
    // ==========================================
    
    // Récupérer le cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Formater les prix
    window.formatPrice = function(price) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'XOF'
        }).format(price);
    };
    
    
    // ==========================================
    // PREVIEW D'IMAGES
    // ==========================================
    
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    let preview = input.parentElement.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'image-preview';
                        preview.style.maxWidth = '200px';
                        preview.style.marginTop = '10px';
                        input.parentElement.appendChild(preview);
                    }
                    preview.src = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });
    
    
    // ==========================================
    // CONFIRMATION DE SUPPRESSION
    // ==========================================
    
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirmDelete || 'Êtes-vous sûr de vouloir supprimer cet élément ?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
});

// Animation de défilement de la page
@keyframes slideOut {
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}