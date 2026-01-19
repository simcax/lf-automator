/**
 * Dashboard JavaScript Module
 * Handles client-side interactivity for the token pool dashboard
 */

/**
 * Show a message to the user
 * @param {string} message - The message to display
 * @param {string} type - The message type: 'success', 'error', or 'info'
 */
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('messageContainer');
    
    // Define color classes based on message type
    const colorClasses = {
        success: 'bg-green-50 border-green-200 text-green-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    
    const iconPaths = {
        success: 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z',
        error: 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z',
        info: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z'
    };
    
    const colors = colorClasses[type] || colorClasses.info;
    const iconPath = iconPaths[type] || iconPaths.info;
    
    messageContainer.innerHTML = `
        <div class="p-4 ${colors} border rounded-lg">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="${iconPath}" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium">${message}</p>
                </div>
            </div>
        </div>
    `;
    
    messageContainer.classList.remove('hidden');
    
    // Auto-hide success messages after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageContainer.classList.add('hidden');
        }, 3000);
    }
}

/**
 * Create HTML for a single pool card
 * @param {Object} pool - Pool data object
 * @returns {string} HTML string for the pool card
 */
function createPoolCard(pool) {
    // Determine state badge HTML
    let stateBadge = '';
    if (pool.state === 'critical') {
        stateBadge = `
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800 border border-red-300">
                <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
                Critical
            </span>
        `;
    } else if (pool.state === 'warning') {
        stateBadge = `
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800 border border-yellow-300">
                <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                Warning
            </span>
        `;
    } else {
        stateBadge = `
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-300">
                <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                Normal
            </span>
        `;
    }
    
    return `
        <div class="pool-card bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200">
            <div class="p-6">
                <!-- Pool Name -->
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Pool #${pool.pool_uuid.substring(0, 8)}</h3>
                
                <!-- Pool State Badge -->
                <div class="mb-4">
                    ${stateBadge}
                </div>
                
                <!-- Pool Details -->
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">Current Count:</span>
                        <span class="text-lg font-bold text-gray-900">${pool.current_count}</span>
                    </div>
                    
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">Start Count:</span>
                        <span class="text-sm text-gray-900">${pool.start_count}</span>
                    </div>
                    
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">Status:</span>
                        <span class="text-sm text-gray-900 capitalize">${pool.pool_status}</span>
                    </div>
                    
                    <div class="pt-3 border-t border-gray-200">
                        <span class="text-xs text-gray-500">Last Updated:</span>
                        <p class="text-xs text-gray-700 mt-1">${pool.pool_date || 'N/A'}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Update the DOM with new pool data
 * @param {Array} pools - Array of pool objects
 */
function updatePoolsDisplay(pools) {
    const poolsContainer = document.getElementById('poolsContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (pools.length === 0) {
        // Show empty state
        if (poolsContainer) {
            poolsContainer.classList.add('hidden');
        }
        if (emptyState) {
            emptyState.classList.remove('hidden');
        }
    } else {
        // Show pools
        if (emptyState) {
            emptyState.classList.add('hidden');
        }
        if (poolsContainer) {
            poolsContainer.classList.remove('hidden');
            poolsContainer.innerHTML = pools.map(pool => createPoolCard(pool)).join('');
        }
    }
}

/**
 * Refresh token pool data from the server
 */
async function refreshPools() {
    const refreshButton = document.getElementById('refreshButton');
    
    try {
        // Disable button and show loading state
        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.innerHTML = `
                <svg class="animate-spin w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
            `;
        }
        
        // Fetch data from API
        const response = await fetch('/api/pools');
        
        if (!response.ok) {
            throw new Error('Failed to fetch pool data');
        }
        
        const pools = await response.json();
        
        // Update the display
        updatePoolsDisplay(pools);
        
        // Show success message
        showMessage('Pool data refreshed successfully', 'success');
        
    } catch (error) {
        console.error('Error refreshing pools:', error);
        showMessage('Failed to refresh pool data. Please try again.', 'error');
    } finally {
        // Re-enable button and restore original text
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.innerHTML = `
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Refresh
            `;
        }
    }
}

/**
 * Show modal dialog for creating a new pool
 */
function showNewPoolModal() {
    // Create modal HTML
    const modalHTML = `
        <div id="newPoolModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium leading-6 text-gray-900 mb-4">Create New Token Pool</h3>
                    <form id="newPoolForm">
                        <div class="mb-4">
                            <label for="tokenCount" class="block text-sm font-medium text-gray-700 mb-2">
                                Token Count
                            </label>
                            <input 
                                type="number" 
                                id="tokenCount" 
                                name="tokenCount" 
                                min="1" 
                                required
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Enter number of tokens"
                            />
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button 
                                type="button" 
                                id="cancelButton"
                                class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
                            >
                                Cancel
                            </button>
                            <button 
                                type="submit"
                                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                Create Pool
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Attach event listeners
    const modal = document.getElementById('newPoolModal');
    const form = document.getElementById('newPoolForm');
    const cancelButton = document.getElementById('cancelButton');
    
    // Close modal on cancel
    cancelButton.addEventListener('click', () => {
        modal.remove();
    });
    
    // Close modal on background click
    modal.addEventListener('click', (e) => {
        if (e.target.id === 'newPoolModal') {
            modal.remove();
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await createNewPool();
    });
    
    // Focus on input
    document.getElementById('tokenCount').focus();
}

/**
 * Create a new token pool via API
 */
async function createNewPool() {
    const tokenCountInput = document.getElementById('tokenCount');
    const tokenCount = parseInt(tokenCountInput.value);
    
    if (!tokenCount || tokenCount <= 0) {
        showMessage('Please enter a valid token count', 'error');
        return;
    }
    
    try {
        // Send POST request to create pool
        const response = await fetch('/api/pools', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token_count: tokenCount,
                pool_status: 'active'
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create pool');
        }
        
        // Close modal
        const modal = document.getElementById('newPoolModal');
        if (modal) {
            modal.remove();
        }
        
        // Show success message
        showMessage('Pool created successfully', 'success');
        
        // Refresh the pools display
        await refreshPools();
        
    } catch (error) {
        console.error('Error creating pool:', error);
        showMessage(error.message || 'Failed to create pool. Please try again.', 'error');
    }
}

/**
 * Initialize event listeners when the page loads
 */
function init() {
    // Attach click handler to refresh button
    const refreshButton = document.getElementById('refreshButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshPools);
    }
    
    // Attach click handler to new pool button
    const newPoolButton = document.getElementById('newPoolButton');
    if (newPoolButton) {
        newPoolButton.addEventListener('click', showNewPoolModal);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
