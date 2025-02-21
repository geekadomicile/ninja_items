export class API {
    static BASE_URL = 'http://localhost:8000/api';

    static async getItems() {
        const response = await fetch(`${this.BASE_URL}/items`);
        if (!response.ok) throw new Error('Failed to fetch items');
        return response.json();
    }

    static async createItem(data) {
        const response = await fetch(`${this.BASE_URL}/items`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create item');
        return response.json();
    }

    static async addNote(itemId, content, author = 'User') {
        const response = await fetch(`${this.BASE_URL}/items/${itemId}/notes`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ content, author })
        });
        if (!response.ok) throw new Error('Failed to add note');
        return response.json();
    }

    static async addFile(itemId, file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${this.BASE_URL}/items/${itemId}/files`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error('Failed to upload file');
        return response.json();
    }

    static async deleteItem(itemId) {
        const response = await fetch(`${this.BASE_URL}/items/${itemId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete item');
    }

    static async moveItem(itemId, newParentId) {
        const response = await fetch(`${this.BASE_URL}/items/${itemId}/move`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ new_parent_id: newParentId || null })
        });
        if (!response.ok) throw new Error('Failed to move item');
        return response.json();
    }

    static async updateListing(itemId, listingData) {
        const response = await fetch(`${this.BASE_URL}/items/${itemId}/listing`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                listing_json: JSON.stringify(listingData)
            })
        });
        if (!response.ok) throw new Error('Failed to update listing');
        return response.json();
    }

    static async exportListing(itemId, itemName, listingData) {
        // Simulate API call by creating a text file
        const content = JSON.stringify(listingData, null, 2);
        const filename = `${itemName.replace(/[^a-z0-9]/gi, '_')}_${itemId}.txt`;
        
        // Create a blob and download it
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}
