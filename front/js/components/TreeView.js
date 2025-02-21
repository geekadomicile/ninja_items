import { API } from '../api.js';

export class TreeView {
    constructor() {
        this.container = document.getElementById('treeView');
        this.items = [];
        this.setupSearch();
    }

    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e));
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

    async loadItems() {
        try {
            this.items = await API.getItems();
            this.render();
            return this.items;
        } catch (error) {
            console.error('Failed to load items:', error);
            return [];
        }
    }

    render() {
        this.container.innerHTML = '';
        this.items.forEach(item => {
            this.container.appendChild(this.renderItem(item));
        });
    }

    renderItem(item) {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'tree-item';

        const itemDetails = document.createElement('div');
        itemDetails.className = 'item-details';

        const content = document.createElement('div');
        content.style.display = 'flex';
        content.style.justifyContent = 'space-between';
        content.style.alignItems = 'start';

        const info = document.createElement('div');
        info.innerHTML = `
            <strong>${item.name}</strong>
            <p>${item.description || 'No description'}</p>
            <div class="path">Path: ${item.full_path}</div>
            <div class="attachments">
                Attachments: ${item.attachment_count}
                ${this.renderNotes(item.notes)}
                ${this.renderFiles(item.files)}
            </div>
        `;

        const actions = document.createElement('div');
        actions.style.display = 'flex';
        actions.style.gap = '5px';

        // Create buttons with bound event listeners
        const buttons = [
            { icon: '📝', handler: () => this.handleAddNote(item.id) },
            { icon: '📎', handler: () => this.handleAddFile(item.id) },
            { icon: '📦', handler: () => this.showMoveModal(item.id) },
            { icon: '🗑️', handler: () => this.handleDelete(item.id) },
            { text: 'Sell', handler: () => this.handleSell(item.id) }
        ];

        buttons.forEach(({ icon, text, handler }) => {
            const button = document.createElement('button');
            button.style.width = 'auto';
            button.style.padding = '5px 10px';
            button.textContent = icon || text;
            button.addEventListener('click', handler);
            actions.appendChild(button);
        });

        content.appendChild(info);
        content.appendChild(actions);
        itemDetails.appendChild(content);
        itemDiv.appendChild(itemDetails);

        if (item.children?.length > 0) {
            const childrenDiv = document.createElement('div');
            childrenDiv.style.marginLeft = '20px';
            item.children.forEach(child => {
                childrenDiv.appendChild(this.renderItem(child));
            });
            itemDiv.appendChild(childrenDiv);
        }

        return itemDiv;
    }

    renderNotes(notes = []) {
        return notes.map(note => `
            <div class="note-item">
                <div class="note-content">${note.content}</div>
                <div class="note-metadata">By ${note.author}</div>
            </div>
        `).join('');
    }

    renderFiles(files = []) {
        return files.map(file => `
            <div class="file-item">
                <a href="${file.file}" target="_blank">${file.file.split('/').pop()}</a>
            </div>
        `).join('');
    }

    async handleAddNote(itemId) {
        const content = prompt('Enter note content:');
        if (!content) return;

        try {
            await API.addNote(itemId, content);
            await this.loadItems();
        } catch (error) {
            console.error('Failed to add note:', error);
        }
    }

    async handleAddFile(itemId) {
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = async () => {
            if (!input.files.length) return;
            try {
                await API.addFile(itemId, input.files[0]);
                await this.loadItems();
            } catch (error) {
                console.error('Failed to upload file:', error);
            }
        };
        input.click();
    }

    populateDestinationDropdown(currentItemId) {
        const select = document.getElementById('newParentId');
        select.innerHTML = '<option value="">No Parent</option>';
        
        // Helper function to add items to dropdown
        const addItemToDropdown = (item) => {
            if (item.id !== currentItemId) {  // Prevent moving to itself
                const option = document.createElement('option');
                option.value = item.id;
                option.textContent = `${item.name} (${item.full_path})`;
                select.appendChild(option);
                
                // Recursively add children
                if (item.children) {
                    item.children.forEach(child => addItemToDropdown(child));
                }
            }
        };

        // Add all items to dropdown
        this.items.forEach(item => addItemToDropdown(item));
    }

    showMoveModal(itemId) {
        document.getElementById('moveItemId').value = itemId;
        this.populateDestinationDropdown(itemId);
        document.getElementById('moveModal').classList.add('active');
    }

    async handleMove(itemId) {
        const moveItemId = document.getElementById('moveItemId').value;
        const newParentId = document.getElementById('newParentId').value;
        
        try {
            await API.moveItem(moveItemId, newParentId);
            document.getElementById('moveModal').classList.remove('active');
            await this.loadItems();
        } catch (error) {
            console.error('Failed to move item:', error);
            alert('Failed to move item. Please try again.');
        }
    }

    async handleDelete(itemId) {
        if (!confirm('Are you sure you want to delete this item?')) return;
        try {
            await API.deleteItem(itemId);
            await this.loadItems();
        } catch (error) {
            console.error('Failed to delete item:', error);
        }
    }

    handleSell(itemId) {
        this.onSell?.(itemId);
    }

    // Callbacks for external handlers
    setOnMove(callback) {
        this.onMove = callback;
    }

    setOnSell(callback) {
        this.onSell = callback;
    }

    getSearchTemplate() {
        return `
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search items...">
            </div>
        `;
    }
}
