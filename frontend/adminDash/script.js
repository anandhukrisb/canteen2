// Polling interval in ms
const POLL_INTERVAL = 5000;

// DOM Elements
const ordersList = document.getElementById('orders-list');
const countBadge = document.getElementById('count-badge');
const navToggle = document.getElementById('nav-toggle');
const mainNav = document.getElementById('main-nav');

function init() {
    // Initial fetch
    fetchOrders();
    fetchStats();

    // Set up polling
    const pollId = setInterval(() => {
        fetchOrders();
        fetchStats();
    }, POLL_INTERVAL);

    // Navbar toggle
    if (navToggle && mainNav) {
        navToggle.addEventListener('click', () => {
            mainNav.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }

    // Event Delegation for "Mark as Done" buttons
    // This handles clicks on dynamically added buttons
    if (ordersList) {
        ordersList.addEventListener('click', (e) => {
            if (e.target.classList.contains('js-mark-done')) {
                const orderId = e.target.getAttribute('data-id');
                markAsDone(orderId);
            }
        });
    }
}

let currentFilter = 'NEW';

function setFilter(status) {
    currentFilter = status;

    // Update active class on buttons
    document.querySelectorAll('.toggle-option').forEach(btn => {
        if (btn.dataset.filter === status) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Toggle slider position
    const toggleSwitch = document.querySelector('.toggle-switch');
    if (toggleSwitch) {
        if (status === 'DELIVERED') {
            toggleSwitch.classList.add('show-done');
        } else {
            toggleSwitch.classList.remove('show-done');
        }
    }

    fetchOrders();
}

async function fetchStats() {
    try {
        const response = await fetch('/get_order_stats/');
        if (!response.ok) return;
        const data = await response.json();

        const countNew = document.getElementById('count-new');
        const countDone = document.getElementById('count-done');

        if (countNew) countNew.textContent = data.new_count;
        if (countDone) countDone.textContent = data.delivered_count;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchOrders() {
    try {
        const response = await fetch(`/get_new_orders/?status=${currentFilter}`);
        if (!response.ok) {
            console.error('Network response was not ok');
            return;
        }
        const html = await response.text();
        ordersList.innerHTML = html;
        updateCount();
    } catch (error) {
        console.error('Error fetching orders:', error);
    }
}

async function markAsDone(orderId) {
    if (!orderId) return;

    try {
        // Robust CSRF token retrieval: try DOM input first (from {% csrf_token %}), then cookie
        let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrftoken) {
            csrftoken = getCookie('csrftoken');
        }

        const response = await fetch(`/mark_order_done/${orderId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        if (response.ok) {
            // Immediate feedback: refresh orders to show updated state
            fetchOrders();
            fetchStats();
        } else {
            console.error('Failed to update status:', response.status);
            if (response.status === 405) {
                alert("Error: Method Not Allowed. Ensure backend accepts POST.");
            }
        }
    } catch (error) {
        console.error('Error updating order:', error);
    }
}

function updateCount() {
    // Count the number of order cards in the list
    if (countBadge && ordersList) {
        const items = ordersList.querySelectorAll('.order-card');
        countBadge.textContent = items.length;
    }
}

// Helper to get CSRF token from cookie
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

// Initialize
document.addEventListener('DOMContentLoaded', init);
