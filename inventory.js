class InventoryManager {
    constructor() {
        this.API_URL = 'http://localhost:8000/api';
        this.items = [];
        this.selectedItemId = null;
        this.init();
    }

    async init() {
        await this.fetchInventory();
        this.setupEventListeners();
        this.setupAttachmentHandlers();
        this.updateParentSelect();
        this.updateItemSelects();
    }

    setupEventListeners() {
        document.getElementById('itemForm').addEventListener('submit', e => this.handleFormSubmit(e));
        document.getElementById('searchInput').addEventListener('input', e => this.handleSearch(e));
    }

    updateItemSelects() {
        // Update all item selection dropdowns with current inventory
        const selects = ['noteItemId', 'fileItemId', 'emailItemId', 'codeItemId']
            .map(id => document.getElementById(id))
            .filter(select => select); // Filter out any null elements

        selects.forEach(select => {
            select.innerHTML = '<option value="">Select an item...</option>';
            this.addOptionsToSelect(select, this.items);
        });
    }

    async fetchInventory() {
        try {
            const response = await fetch(`${this.API_URL}/items`);
            if (!response.ok) {
                throw new Error(`Failed to fetch inventory: ${response.statusText}`);
            }
            this.items = await response.json();
            this.renderInventoryTree();
            this.updateItemSelects(); // Update attachment form selects
        } catch (error) {
            console.error('Failed to fetch inventory:', error);
            alert('Failed to load inventory. Please refresh the page.');
        }
    }

    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        const items = document.querySelectorAll('.tree-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        const formData = {
            name: document.getElementById('name').value,
            description: document.getElementById('description').value,
            qr_code: document.getElementById('qr_code').value,
            parent_id: document.getElementById('parent_id').value || null
        };

        try {
            const response = await fetch(`${this.API_URL}/items`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                await this.fetchInventory();
                e.target.reset();
            }
        } catch (error) {
            console.error('Failed to add item:', error);
        }
    }

    renderInventoryTree() {
        const treeView = document.getElementById('treeView');
        treeView.innerHTML = '';
        this.items.forEach(item => treeView.appendChild(this.renderItem(item)));
        this.updateParentSelect();
    }

    renderItem(item) {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'tree-item';
        itemDiv.innerHTML = this.getItemHTML(item);

        if (item.children?.length) {
            const childrenDiv = document.createElement('div');
            childrenDiv.style.marginLeft = '20px';
            item.children.forEach(child => childrenDiv.appendChild(this.renderItem(child)));
            itemDiv.appendChild(childrenDiv);
        }

        return itemDiv;
    }

    setupAttachmentHandlers() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
    
        // Form submissions
        document.getElementById('noteForm').addEventListener('submit', e => this.handleNoteSubmit(e));
        document.getElementById('fileForm').addEventListener('submit', e => this.handleFileSubmit(e));
        document.getElementById('emailForm').addEventListener('submit', e => this.handleEmailSubmit(e));
        document.getElementById('codeForm').addEventListener('submit', e => this.handleCodeSubmit(e));
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }
    
    async handleNoteSubmit(e) {
        e.preventDefault();
        const itemId = document.getElementById('noteItemId').value;
        const content = document.getElementById('noteContent').value;
        
        if (!itemId || !content) {
            alert('Please select an item and enter note content');
            return;
        }

        try {
            const response = await fetch(`${this.API_URL}/items/${itemId}/notes`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    content: content,
                    author: 'User' // We can make this configurable later
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to add note: ${response.statusText}`);
            }

            await this.fetchInventory(); // Refresh the view
            e.target.reset();
        } catch (error) {
            console.error('Failed to add note:', error);
            alert('Failed to add note. Please try again.');
        }
    }
    
    async handleFileSubmit(e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append('item_id', document.getElementById('fileItemId').value);
        formData.append('file', document.getElementById('fileInput').files[0]);
        
        await this.submitAttachment('files', formData, true);
        e.target.reset();
    }
    
    async handleEmailSubmit(e) {
        e.preventDefault();
        const data = {
            item_id: document.getElementById('emailItemId').value,
            subject: document.getElementById('emailSubject').value,
            from_address: document.getElementById('emailFrom').value,
            body: document.getElementById('emailBody').value,
            received_at: new Date().toISOString()
        };
        
        await this.submitAttachment('emails', data);
        e.target.reset();
    }
    
    async handleCodeSubmit(e) {
        e.preventDefault();
        const data = {
            item_id: document.getElementById('codeItemId').value,
            code: document.getElementById('codeValue').value,
            source: document.getElementById('codeSource').value
        };
        
        await this.submitAttachment('codes', data);
        e.target.reset();
    }
    
    async submitAttachment(type, data, isFormData = false) {
        try {
            const options = {
                method: 'POST',
                headers: isFormData ? {} : {'Content-Type': 'application/json'},
                body: isFormData ? data : JSON.stringify(data)
            };
            
            const response = await fetch(`${this.API_URL}/items/attachments/${type}`, options);
            if (response.ok) {
                await this.fetchInventory();
            }
        } catch (error) {
            console.error(`Failed to add ${type}:`, error);
        }
    }
    

    getItemHTML(item) {
        return `
            <div class="item-details">
                <div class="item-header">
                    <strong>${item.name}</strong>
                    <div class="actions">
                        <button class="btn-move" onclick="inventoryManager.showMoveModal(${item.id})">Move</button>
                        <button class="btn-delete" onclick="inventoryManager.deleteItem(${item.id})">Delete</button>
                    </div>
                </div>
                <p>${item.description || 'No description'}</p>
                <div class="metadata">
                    <div>Path: ${item.full_path}</div>
                    <div>QR Code: ${item.qr_code || 'N/A'}</div>
                    <div>Created: ${new Date(item.created_at).toLocaleString()}</div>
                </div>
                <div class="attachments-list">
                    ${this.renderAttachments(item)}
                </div>
            </div>
        `;
    }

    updateParentSelect() {
        const selects = ['parent_id', 'newParentId'].map(id => document.getElementById(id));
        selects.forEach(select => {
            if (!select) return;
            select.innerHTML = '<option value="">No Parent</option>';
            this.addOptionsToSelect(select, this.items);
        });
    }

    addOptionsToSelect(select, items, level = 0) {
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = '─'.repeat(level) + ' ' + item.name;
            select.appendChild(option);
            if (item.children?.length) {
                this.addOptionsToSelect(select, item.children, level + 1);
            }
        });
    }

    async deleteItem(id) {
        if (!confirm('Are you sure you want to delete this item?')) return;
        try {
            await fetch(`${this.API_URL}/items/${id}`, { method: 'DELETE' });
            await this.fetchInventory();
        } catch (error) {
            console.error('Failed to delete item:', error);
        }
    }

    showMoveModal(id) {
        this.selectedItemId = id;
        document.getElementById('moveModal').style.display = 'block';
        this.updateParentSelect();
    }

    closeModal() {
        document.getElementById('moveModal').style.display = 'none';
        this.selectedItemId = null;
    }
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    renderAttachments(item) {
        const attachments = [];
        
        // Add quick action buttons
        attachments.push(`
            <div class="attachments-header">
                <h4>Attachments</h4>
                <div class="quick-actions">
                    <button class="btn-icon" onclick="inventoryManager.showInlineNoteForm(${item.id})" title="Add Note">📝</button>
                    <button class="btn-icon" onclick="inventoryManager.showInlineFileForm(${item.id})" title="Upload File">📎</button>
                </div>
            </div>
            <div id="inlineNoteForm-${item.id}" class="inline-form">
                <div class="form-group">
                    <textarea id="inlineNoteContent-${item.id}" rows="2" placeholder="Enter note"></textarea>
                </div>
                <div class="actions">
                    <button class="btn-small" onclick="inventoryManager.submitInlineNote(${item.id})">Save</button>
                    <button class="btn-small" onclick="inventoryManager.hideInlineForm(${item.id}, 'note')">Cancel</button>
                </div>
            </div>
            <div id="inlineFileForm-${item.id}" class="inline-form">
                <div class="form-group">
                    <input type="file" id="inlineFileInput-${item.id}">
                </div>
                <div class="actions">
                    <button class="btn-small" onclick="inventoryManager.submitInlineFile(${item.id})">Upload</button>
                    <button class="btn-small" onclick="inventoryManager.hideInlineForm(${item.id}, 'file')">Cancel</button>
                </div>
            </div>
        `);
        
        if (item.notes?.length) {
            attachments.push(`<div class="attachment-group">
                <strong>Notes (${item.notes.length})</strong>
                ${item.notes.map(note => `
                    <div class="note-item">
                        <div class="note-content">${this.escapeHtml(note.content)}</div>
                        <div class="note-metadata">
                            By ${this.escapeHtml(note.author)} - ${new Date(note.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('')}
            </div>`);
        }
        
        if (item.files?.length) {
            attachments.push(`<div class="attachment-group">
                <strong>Files (${item.files.length})</strong>
                ${item.files.map(file => `
                    <div class="file-item">
                        <a href="${this.escapeHtml(file.file)}" target="_blank" class="file-link">
                            <span class="file-icon">📄</span>
                            <span class="file-info">
                                <span class="file-name">${this.escapeHtml(file.file.split('/').pop())}</span>
                                <span class="file-type">${this.escapeHtml(file.file_type)}</span>
                            </span>
                        </a>
                    </div>
                `).join('')}
            </div>`);
        }
        
        return attachments.join('') || 'No attachments';
    }

    showInlineNoteForm(itemId) {
        document.getElementById(`inlineNoteForm-${itemId}`).classList.add('active');
    }

    showInlineFileForm(itemId) {
        document.getElementById(`inlineFileForm-${itemId}`).classList.add('active');
    }

    hideInlineForm(itemId, type) {
        document.getElementById(`inline${type.charAt(0).toUpperCase() + type.slice(1)}Form-${itemId}`).classList.remove('active');
    }

    async submitInlineNote(itemId) {
        const content = document.getElementById(`inlineNoteContent-${itemId}`).value;
        
        if (!content) {
            alert('Please enter note content');
            return;
        }

        try {
            const response = await fetch(`${this.API_URL}/items/${itemId}/notes`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    content: content,
                    author: 'User'
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to add note: ${response.statusText}`);
            }

            await this.fetchInventory();
            this.hideInlineForm(itemId, 'note');
        } catch (error) {
            console.error('Failed to add note:', error);
            alert('Failed to add note. Please try again.');
        }
    }

    async submitInlineFile(itemId) {
        const fileInput = document.getElementById(`inlineFileInput-${itemId}`);
        if (!fileInput.files.length) {
            alert('Please select a file');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch(`${this.API_URL}/items/${itemId}/files`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Failed to upload file: ${error}`);
            }

            await this.fetchInventory();
            this.hideInlineForm(itemId, 'file');
            document.getElementById(`inlineFileInput-${itemId}`).value = ''; // Clear the file input
        } catch (error) {
            console.error('Failed to upload file:', error);
            alert('Failed to upload file. Please try again.');
        }
    }

    // Helper method to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async confirmMove() {
        const newParentId = document.getElementById('newParentId').value;
        try {
            await fetch(`${this.API_URL}/items/${this.selectedItemId}/move`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ new_parent_id: newParentId || null })
            });
            this.closeModal();
            await this.fetchInventory();
        } catch (error) {
            console.error('Failed to move item:', error);
        }
    }
}
