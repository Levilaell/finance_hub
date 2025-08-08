/* Custom Admin JavaScript for Finance Hub */

(function() {
    'use strict';
    
    // Add confirmation for dangerous actions
    document.addEventListener('DOMContentLoaded', function() {
        // Confirm deletions
        const deleteButtons = document.querySelectorAll('.deletelink');
        deleteButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                    e.preventDefault();
                    return false;
                }
            });
        });
        
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl+S to save
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                const saveButton = document.querySelector('.submit-row input[name="_save"]');
                if (saveButton) {
                    saveButton.click();
                }
            }
            
            // Escape to cancel
            if (e.key === 'Escape') {
                const cancelLink = document.querySelector('.submit-row a.cancel-link');
                if (cancelLink) {
                    window.location.href = cancelLink.href;
                }
            }
        });
        
        // Auto-save draft for long forms
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            let timeout;
            form.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(function() {
                    // Save form data to localStorage
                    const formData = new FormData(form);
                    const data = {};
                    formData.forEach((value, key) => {
                        data[key] = value;
                    });
                    localStorage.setItem('admin_draft_' + window.location.pathname, JSON.stringify(data));
                    showNotification('Draft saved', 'info');
                }, 5000);
            });
        });
        
        // Restore draft if exists
        const draftKey = 'admin_draft_' + window.location.pathname;
        const draft = localStorage.getItem(draftKey);
        if (draft) {
            if (confirm('A draft was found. Do you want to restore it?')) {
                const data = JSON.parse(draft);
                Object.keys(data).forEach(key => {
                    const field = document.querySelector(`[name="${key}"]`);
                    if (field) {
                        field.value = data[key];
                    }
                });
                localStorage.removeItem(draftKey);
            }
        }
        
        // Enhanced search with debouncing
        const searchInput = document.querySelector('#searchbar');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function(e) {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(function() {
                    // Auto-submit search after 500ms of no typing
                    searchInput.form.submit();
                }, 500);
            });
        }
        
        // Show query count if in debug mode
        if (window.DJANGO_DEBUG) {
            const queryCount = document.createElement('div');
            queryCount.className = 'query-count';
            queryCount.textContent = 'Queries: Loading...';
            document.body.appendChild(queryCount);
        }
    });
    
    // Utility function to show notifications
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'success' ? '#27ae60' : '#3498db'};
            color: white;
            border-radius: 4px;
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(function() {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(function() {
                notification.remove();
            }, 300);
        }, 3000);
    }
    
    // Add animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
})();