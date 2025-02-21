import { API } from '../api.js';

export class ListingForm {
    constructor() {
        // Elements will be initialized after DOM insertion
    }

    initForm() {
        this.form = document.getElementById('listingForm');
        this.modal = document.getElementById('listingModal');
        if (!this.form || !this.modal) {
            console.error('Could not find form or modal elements');
            return;
        }
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Close button handler
        const closeBtn = this.modal.querySelector('.close-modal');
        closeBtn.addEventListener('click', () => this.close());
    }

    open(itemId) {
        document.getElementById('listingItemId').value = itemId;
        this.modal.classList.add('active');
    }

    close() {
        this.modal.classList.remove('active');
        this.form.reset();
    }

    async handleSubmit(e) {
        e.preventDefault();
        const itemId = document.getElementById('listingItemId').value;
        const listingData = {
            subject: document.getElementById('subject').value,
            category: document.getElementById('category').value,
            subcategory: document.getElementById('subcategory').value,
            brand: document.getElementById('brand').value,
            type: document.getElementById('type').value,
            usage: document.getElementById('usage').value,
            condition: document.getElementById('condition').value,
            description: document.getElementById('listing_description').value,
            price: document.getElementById('price').value,
            location: document.getElementById('location').value
        };

        try {
            // First update the listing in the database
            const updatedItem = await API.updateListing(itemId, listingData);
            
            // Then export the listing data to a file
            await API.exportListing(itemId, listingData.subject, listingData);
            
            this.close();
            this.onSuccess?.();
        } catch (error) {
            console.error('Failed to update or export listing:', error);
        }
    }

    // Callback for success
    setOnSuccess(callback) {
        this.onSuccess = callback;
    }

    getTemplate() {
        return `
            <form id="listingForm">
                <input type="hidden" id="listingItemId">
                <div class="form-group">
                    <label>Subject</label>
                    <input type="text" id="subject" required>
                </div>
                <div class="form-group">
                    <label>Category</label>
                    <select id="category" required>
                        <option value="Électronique">Électronique</option>
                        <option value="Informatique">Informatique</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Subcategory</label>
                    <select id="subcategory" required>
                        <option value="Ordinateurs">Ordinateurs</option>
                        <option value="Composants">Composants</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Brand</label>
                    <input type="text" id="brand" required>
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <input type="text" id="type" required>
                </div>
                <div class="form-group">
                    <label>Usage</label>
                    <select id="usage" required>
                        <option value="Polyvalent">Polyvalent</option>
                        <option value="Gaming">Gaming</option>
                        <option value="Bureautique">Bureautique</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Condition</label>
                    <select id="condition" required>
                        <option value="Neuf">Neuf</option>
                        <option value="Très bon état">Très bon état</option>
                        <option value="Bon état">Bon état</option>
                        <option value="État moyen">État moyen</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="listing_description" rows="4" required></textarea>
                </div>
                <div class="form-group">
                    <label>Price (€)</label>
                    <input type="number" id="price" required min="0">
                </div>
                <div class="form-group">
                    <label>Location</label>
                    <input type="text" id="location" required>
                </div>
                <button type="submit">Generate Listing</button>
            </form>
        `;
    }
}
