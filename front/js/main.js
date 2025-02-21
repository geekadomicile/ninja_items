import { ItemForm } from './forms/ItemForm.js';
import { ListingForm } from './forms/ListingForm.js';
import { TreeView } from './components/TreeView.js';

class App {
    constructor() {
        console.log('Initializing App...');
        try {
            // Inject templates
            const itemFormTemplate = new ItemForm().getTemplate();
            const listingFormTemplate = new ListingForm().getTemplate();
            const searchTemplate = new TreeView().getSearchTemplate();

            console.log('Templates loaded');

            document.getElementById('itemFormContainer').innerHTML = itemFormTemplate;
            document.getElementById('listingFormContainer').innerHTML = listingFormTemplate;
            document.getElementById('searchContainer').innerHTML = searchTemplate;

            console.log('Templates injected');

            // Initialize components after DOM insertion
            this.itemForm = new ItemForm();
            this.itemForm.initForm();
            
            this.listingForm = new ListingForm();
            this.listingForm.initForm(); 
            this.treeView = new TreeView();

            console.log('Components initialized');

            // Setup callbacks
            this.setupCallbacks();

            // Initial load
            this.treeView.loadItems()
                .then(items => {
                    console.log('Items loaded:', items);
                    // Update parent selects
                    this.itemForm.updateParentSelect(items);
                    const moveSelect = document.getElementById('newParentId');
                    moveSelect.innerHTML = '<option value="">No Parent</option>';
                    this.addOptionsToSelect(moveSelect, items);
                })
                .catch(error => {
                    console.error('Failed to load items:', error);
                });
        } catch (error) {
            console.error('Initialization error:', error);
        }
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

    setupCallbacks() {
        // When item form submits successfully, reload tree and update parent selects
        this.itemForm.setOnSuccess(async () => {
            const items = await this.treeView.loadItems();
            this.itemForm.updateParentSelect(items);
        });

        // When listing form submits successfully, reload tree
        this.listingForm.setOnSuccess(() => {
            this.treeView.loadItems();
        });

        // When sell button clicked, open listing form
        this.treeView.setOnSell((itemId) => {
            this.listingForm.open(itemId);
        });

        // When move button clicked, show move modal
        this.treeView.setOnMove((itemId) => {
            document.getElementById('moveModal').classList.add('active');
            document.getElementById('moveItemId').value = itemId;
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    // Make app's treeView instance global for button click handlers
    window.treeView = app.treeView;
});
