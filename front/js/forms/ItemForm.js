import { API } from '../api.js';

export class ItemForm {
    constructor() {
        // Form will be initialized after DOM insertion
    }

    initForm() {
        this.form = document.getElementById('itemForm');
        if (!this.form) {
            console.error('Could not find form element with id "itemForm"');
            return;
        }
        this.setupEventListeners();
        this.updateParentSelect([]);
    }

    updateParentSelect(items, level = 0) {
        const select = document.getElementById('parent_id');
        if (!select) return;

        if (level === 0) {
            select.innerHTML = '<option value="">No Parent</option>';
        }

        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = '─'.repeat(level) + ' ' + item.name;
            select.appendChild(option);

            if (item.children?.length) {
                this.updateParentSelect(item.children, level + 1);
            }
        });
    }

    setupEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();
        const formData = {
            name: document.getElementById('name').value,
            description: document.getElementById('description').value.trim(),
            qr_code: document.getElementById('qr_code').value,
            parent_id: document.getElementById('parent_id').value || null
        };

        // Don't send empty description
        if (!formData.description) {
            delete formData.description;
        }

        try {
            // Create the item
            const result = await API.createItem(formData);
            const itemId = result.id;

            // Add note if provided
            const noteContent = document.getElementById('initial_note').value;
            if (noteContent) {
                await API.addNote(itemId, noteContent);
            }

            // Add file if provided
            const fileInput = document.getElementById('initial_file');
            if (fileInput.files.length > 0) {
                await API.addFile(itemId, fileInput.files[0]);
            }

            // Reset form
            this.form.reset();

            // Notify success
            this.onSuccess?.();
        } catch (error) {
            console.error('Failed to add item:', error);
        }
    }

    // Callback for success
    setOnSuccess(callback) {
        this.onSuccess = callback;
    }

    getTemplate() {
        return `
            <form id="itemForm">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" id="name" required>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="description" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label>QR Code</label>
                    <input type="text" id="qr_code">
                </div>
                <div class="form-group">
                    <label>Parent Item</label>
                    <select id="parent_id">
                        <option value="">No Parent</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Note</label>
                    <textarea id="initial_note" rows="3" placeholder="Add a note (optional)"></textarea>
                </div>
                <div class="form-group">
                    <label>File</label>
                    <input type="file" id="initial_file">
                </div>
                <button type="submit">Add Item</button>
            </form>
        `;
    }
}
