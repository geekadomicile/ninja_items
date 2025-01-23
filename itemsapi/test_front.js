const { createApp } = Vue

createApp({
    data() {
        return {
            apiBase: 'http://localhost:8000',
            items: [],
            treeItems: [],
            computers: [], // Items without parents
            newItem: {
                name: '',
                description: '',
                parent_id: null
            },
            search: {
                name: '',
                description: '',
                qr_code: ''
            },
            searchResults: null,
            viewMode: 'flat',
            isLoading: false,
            successMessage: null,
            componentHistory: []
        }
    },
    computed: {
        displayedItems() {
            if (this.searchResults !== null) {
                return this.searchResults
            }
            return this.viewMode === 'flat' ? this.items : this.treeItems
        }
    },
    methods: {
        showSuccess(message) {
            this.successMessage = message
            setTimeout(() => {
                this.successMessage = null
            }, 3000)
        },
                
        
        initializeItem(item) {
            return {
                ...item,
                newEmail: { subject: '', content: '' },
                newNote: '',
                newParentId: '',
                newSubItem: { name: '', description: '' }
            }
        },
        
        async fetchWithLoading(url, options = {}) {
            this.isLoading = true
            try {
                const response = await fetch(`${this.apiBase}${url}`, {
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                })
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
                return await response.json()
            } finally {
                this.isLoading = false
            }
        },
        
        async performSearch() {
            if (!this.search.name && !this.search.description && !this.search.qr_code) {
                this.searchResults = null
                await this.refreshView()
                return
            }

            const params = new URLSearchParams()
            if (this.search.name) params.append('name', this.search.name)
            if (this.search.description) params.append('description', this.search.description)
            if (this.search.qr_code) params.append('qr_code', this.search.qr_code)

            try {
                const data = await this.fetchWithLoading(`/api/items/search?${params}`)
                this.searchResults = data.map(this.initializeItem)
            } catch (error) {
                console.error('Error searching items:', error)
            }
        },
        
        async fetchItems() {
            try {
                const data = await this.fetchWithLoading('/api/items')
                this.items = data.map(this.initializeItem)
                this.computers = this.items.filter(item => !item.parent_id)
            } catch (error) {
                console.error('Error fetching items:', error)
            }
        },
        
        async fetchTreeItems() {
            try {
                const data = await this.fetchWithLoading('/api/items?hierarchical=true')
                this.treeItems = data.map(this.initializeItem)
            } catch (error) {
                console.error('Error fetching tree items:', error)
            }
        },
        
        async fetchComponentHistory() {
            try {
                const data = await this.fetchWithLoading('/api/items/history')
                this.componentHistory = data
            } catch (error) {
                console.error('Error fetching history:', error)
            }
        },
        
        async createItem() {
            try {
                await this.fetchWithLoading('/api/items', {
                    method: 'POST',
                    body: JSON.stringify(this.newItem)
                })
                this.showSuccess('Item created successfully')
                await this.refreshView()
                this.newItem.name = ''
                this.newItem.description = ''
                this.newItem.parent_id = null
            } catch (error) {
                console.error('Error creating item:', error)
            }
        },
        
        async deleteItem(itemId) {
            if (!confirm('Are you sure you want to delete this item?')) return
            try {
                await this.fetchWithLoading(`/api/items/${itemId}`, {
                    method: 'DELETE'
                })
                this.showSuccess('Item deleted successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error deleting item:', error)
            }
        },

        async installInComputer(componentId, computerId) {
            if (!computerId) {
                alert('Please select a computer')
                return
            }
            await this.changeParent(componentId, computerId)
            this.showSuccess('Component installed successfully')
        },

        async removeFromComputer(componentId) {
            await this.changeParent(componentId, null)
            this.showSuccess('Component removed successfully')
        },

        async changeParent(itemId, newParentId) {
            try {
                await this.fetchWithLoading(`/api/items/${itemId}/parent`, {
                    method: 'PUT',
                    body: JSON.stringify({new_parent_id: newParentId})
                })
                await this.fetchComponentHistory()
                await this.refreshView()
            } catch (error) {
                console.error('Error changing parent:', error)
            }
        },

        async addNote(itemId, content) {
            try {
                await this.fetchWithLoading(`/api/items/${itemId}/notes`, {
                    method: 'POST',
                    body: JSON.stringify({content})
                })
                this.showSuccess('Note added successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error adding note:', error)
            }
        },

        async deleteNote(itemId, noteId) {
            try {
                await this.fetchWithLoading(`/api/items/${itemId}/notes/${noteId}`, {
                    method: 'DELETE'
                })
                this.showSuccess('Note deleted successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error deleting note:', error)
            }
        },

        async addEmail(itemId, emailData) {
            try {
                await this.fetchWithLoading(`/api/items/${itemId}/emails`, {
                    method: 'POST',
                    body: JSON.stringify(emailData)
                })
                this.showSuccess('Email added successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error adding email:', error)
            }
        },

        async deleteEmail(itemId, emailId) {
            try {
                await this.fetchWithLoading(`/api/items/${itemId}/emails/${emailId}`, {
                    method: 'DELETE'
                })
                this.showSuccess('Email deleted successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error deleting email:', error)
            }
        },

        async handleFileUpload(event, itemId) {
            const file = event.target.files[0]
            if (!file) return

            const formData = new FormData()
            formData.append('file', file)

            try {
                await fetch(`${this.apiBase}/api/items/${itemId}/attachments`, {
                    method: 'POST',
                    body: formData
                })
                this.showSuccess('File uploaded successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error uploading file:', error)
            }
        },

        async deleteAttachment(itemId, attachmentId) {
            try {
                await this.fetchWithLoading(`/api/items/${itemId}/attachments/${attachmentId}`, {
                    method: 'DELETE'
                })
                this.showSuccess('Attachment deleted successfully')
                await this.refreshView()
            } catch (error) {
                console.error('Error deleting attachment:', error)
            }
        },

        async refreshView() {
            if (this.viewMode === 'flat') {
                await this.fetchItems()
            } else {
                await this.fetchTreeItems()
            }
        },

        async switchView(mode) {
            this.viewMode = mode
            await this.refreshView()
        }
    },
    mounted() {
        this.refreshView()
        this.fetchComponentHistory()
    }
}).mount('#app')

