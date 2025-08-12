document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Function to activate a specific tab
    function activateTab(tabId) {
        // Remove active class from all buttons and contents
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Add active class to specified tab button and content
        const targetButton = document.querySelector(`.tab-button[data-tab="${tabId}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
        }
        const targetContent = document.getElementById(tabId);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    }
    
    // Check if we should activate the Stats tab from the week page
    if (sessionStorage.getItem('activateStatsTab') === 'true') {
        activateTab('stats');
        sessionStorage.removeItem('activateStatsTab');
    }
    
    // Set up click handlers for tabs
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            activateTab(tabId);
        });
    });
    
    // Style failed attempts cells based on their values
    const failedCells = document.querySelectorAll('.failed-attempts');
    failedCells.forEach(cell => {
        if (cell.textContent === '0') {
            cell.style.backgroundColor = 'transparent';
            cell.style.color = '#d7dadc';
            cell.style.fontWeight = 'normal';
        }
    });
});
        