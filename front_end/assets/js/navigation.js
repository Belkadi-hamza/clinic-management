/**
 * Navigation Helper for Cabinet Management System
 * Provides utilities for page navigation and route management
 */

class NavigationHelper {
    constructor() {
        this.baseUrl = '/app';
        this.routes = null;
        this.currentRoute = this.getCurrentRoute();
    }

    /**
     * Get current route from URL
     */
    getCurrentRoute() {
        const path = window.location.pathname;
        return path.replace(this.baseUrl, '') || '/';
    }

    /**
     * Load routes information from server
     */
    async loadRoutes() {
        try {
            const response = await fetch(`${this.baseUrl}/routes`);
            this.routes = await response.json();
            return this.routes;
        } catch (error) {
            console.error('Failed to load routes:', error);
            return null;
        }
    }

    /**
     * Get all available routes
     */
    async getAllRoutes() {
        if (!this.routes) {
            await this.loadRoutes();
        }
        return this.routes?.all_routes || [];
    }

    /**
     * Get routes by category
     */
    async getRoutesByCategory() {
        if (!this.routes) {
            await this.loadRoutes();
        }
        return this.routes?.categories || {};
    }

    /**
     * Navigate to a specific route
     */
    navigateTo(route) {
        if (!route.startsWith('/')) {
            route = '/' + route;
        }
        window.location.href = `${this.baseUrl}${route}`;
    }

    /**
     * Navigate to a specific route with parameters
     */
    navigateToWithParams(route, params = {}) {
        if (!route.startsWith('/')) {
            route = '/' + route;
        }
        
        const url = new URL(`${this.baseUrl}${route}`, window.location.origin);
        Object.keys(params).forEach(key => {
            url.searchParams.set(key, params[key]);
        });
        
        window.location.href = url.toString();
    }

    /**
     * Get page information for a route
     */
    async getPageInfo(route) {
        try {
            const response = await fetch(`${this.baseUrl}/page-info${route}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to get page info:', error);
            return null;
        }
    }

    /**
     * Get breadcrumb for current or specified route
     */
    async getBreadcrumb(route = null) {
        const currentRoute = route || this.currentRoute;
        try {
            const response = await fetch(`${this.baseUrl}/page-info${currentRoute}`);
            const pageInfo = await response.json();
            
            // Generate breadcrumb based on page info
            const breadcrumb = [
                { title: 'Home', route: '/', active: false }
            ];
            
            if (pageInfo) {
                breadcrumb.push({
                    title: pageInfo.title,
                    route: currentRoute,
                    active: true
                });
            }
            
            return breadcrumb;
        } catch (error) {
            console.error('Failed to get breadcrumb:', error);
            return [{ title: 'Home', route: '/', active: false }];
        }
    }

    /**
     * Generate navigation menu
     */
    async generateNavigationMenu() {
        const categories = await this.getRoutesByCategory();
        return Object.keys(categories).map(categoryKey => ({
            name: categories[categoryKey].name,
            key: categoryKey,
            pages: categories[categoryKey].pages.map(page => ({
                title: page.title,
                route: page.route,
                description: page.description,
                isActive: page.route === this.currentRoute
            }))
        }));
    }

    /**
     * Check if a route exists
     */
    async routeExists(route) {
        const allRoutes = await this.getAllRoutes();
        return allRoutes.some(r => r.route === route);
    }

    /**
     * Get routes for a specific category
     */
    async getRoutesForCategory(category) {
        try {
            const response = await fetch(`${this.baseUrl}/routes/${category}`);
            return await response.json();
        } catch (error) {
            console.error(`Failed to get routes for category ${category}:`, error);
            return null;
        }
    }

    /**
     * Update page title based on current route
     */
    async updatePageTitle() {
        const pageInfo = await this.getPageInfo(this.currentRoute);
        if (pageInfo) {
            document.title = `${pageInfo.title} - Cabinet Management`;
        }
    }

    /**
     * Initialize navigation
     */
    async init() {
        await this.loadRoutes();
        await this.updatePageTitle();
        
        // Add navigation event listeners
        this.addNavigationListeners();
    }

    /**
     * Add navigation event listeners
     */
    addNavigationListeners() {
        // Listen for navigation clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[data-route]');
            if (link) {
                e.preventDefault();
                const route = link.getAttribute('data-route');
                this.navigateTo(route);
            }
        });

        // Listen for back/forward navigation
        window.addEventListener('popstate', () => {
            this.currentRoute = this.getCurrentRoute();
            this.updatePageTitle();
        });
    }

    /**
     * Create navigation link element
     */
    createNavLink(route, title, options = {}) {
        const link = document.createElement('a');
        link.href = `${this.baseUrl}${route}`;
        link.textContent = title;
        link.setAttribute('data-route', route);
        
        if (options.className) {
            link.className = options.className;
        }
        
        if (options.active && route === this.currentRoute) {
            link.classList.add('active');
        }
        
        return link;
    }

    /**
     * Generate breadcrumb HTML
     */
    async generateBreadcrumbHTML() {
        const breadcrumb = await this.getBreadcrumb();
        
        const breadcrumbHTML = breadcrumb.map((item, index) => {
            if (item.active) {
                return `<li class="breadcrumb-item active" aria-current="page">${item.title}</li>`;
            } else {
                return `<li class="breadcrumb-item"><a href="${this.baseUrl}${item.route}">${item.title}</a></li>`;
            }
        }).join('');
        
        return `<nav aria-label="breadcrumb"><ol class="breadcrumb">${breadcrumbHTML}</ol></nav>`;
    }

    /**
     * Generate navigation menu HTML
     */
    async generateNavigationHTML() {
        const menu = await this.generateNavigationMenu();
        
        const menuHTML = menu.map(category => `
            <div class="nav-category">
                <h6 class="nav-category-title">${category.name}</h6>
                <ul class="nav-category-list">
                    ${category.pages.map(page => `
                        <li class="nav-item ${page.isActive ? 'active' : ''}">
                            <a href="${this.baseUrl}${page.route}" 
                               class="nav-link" 
                               data-route="${page.route}"
                               title="${page.description}">
                                ${page.title}
                            </a>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `).join('');
        
        return menuHTML;
    }
}

// Create global navigation instance
window.navigation = new NavigationHelper();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.navigation.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationHelper;
}
