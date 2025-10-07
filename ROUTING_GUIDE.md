# HTML Routing System for Cabinet Management

This guide explains how to use the new HTML routing system that provides organized navigation for all HTML pages in the Cabinet Management application.

## Overview

The routing system provides:
- **Organized route mapping** for all HTML pages
- **Dynamic navigation** with JavaScript helpers
- **Breadcrumb generation** for better UX
- **Route validation** and error handling
- **Category-based organization** of pages

## Architecture

### Backend Components

1. **`backend/html_routes.py`** - Main routing module
2. **`backend/app.py`** - Integration with FastAPI app
3. **Route categories** - Organized page groupings

### Frontend Components

1. **`assets/js/navigation.js`** - JavaScript navigation helper
2. **`route-demo.html`** - Demonstration page
3. **Static file serving** - Existing HTML files

## Route Categories

The system organizes pages into logical categories:

### Main Pages
- `/` - Dashboard
- `/login` - Login page
- `/loading` - Loading screen

### Patient Management
- `/patients` - Patient list
- `/add-patient` - Add new patient
- `/edit-patient` - Edit patient
- `/patient-details` - Patient overview
- `/patient-details/appointments` - Patient appointments
- `/patient-details/billings` - Patient billing
- `/patient-details/documents` - Patient documents
- `/patient-details/lab-results` - Lab results
- `/patient-details/medical-history` - Medical history
- `/patient-details/prescription` - Prescriptions
- `/patient-details/visit-history` - Visit history
- `/patient-details/vital-signs` - Vital signs

### Doctor Management
- `/doctors` - Doctor list
- `/add-doctors` - Add new doctor
- `/edit-doctors` - Edit doctor
- `/doctor-details` - Doctor profile

### Appointment Management
- `/appointments` - Appointment management
- `/appointment-consultation` - Consultation

### Visit Management
- `/visits` - Visit management
- `/start-visits` - Start new visit

### Medical Services
- `/lab-results` - Laboratory results
- `/medical-results` - Medical test results
- `/pharmacy` - Pharmacy management

### Staff Management
- `/staffs` - Staff management

### Settings
- `/general-settings` - General settings
- `/permission-settings` - Permission management
- `/roles` - Role management
- `/security-settings` - Security settings

### Additional Pages
- `/charts` - Data visualization
- `/chat` - Communication
- `/contacts` - Contact management
- `/email` - Email management
- `/file-manager` - File management
- `/forms` - Form management
- `/invoices` - Invoice management
- `/tables` - Data tables
- `/ui` - UI components

## API Endpoints

### Get All Routes
```http
GET /app/routes
```

Returns information about all available routes organized by category.

### Get Routes by Category
```http
GET /app/routes/{category}
```

Returns routes for a specific category.

### Get Page Information
```http
GET /app/page-info/{route}
```

Returns detailed information about a specific page route.

### Navigate to Page
```http
GET /app/{route}
```

Serves the HTML page for the specified route.

## JavaScript Navigation Helper

### Basic Usage

```javascript
// Initialize navigation
await navigation.init();

// Navigate to a page
navigation.navigateTo('/patients');

// Navigate with parameters
navigation.navigateToWithParams('/patient-details', { id: 123 });

// Get current route
const currentRoute = navigation.getCurrentRoute();

// Check if route exists
const exists = await navigation.routeExists('/patients');

// Get page information
const pageInfo = await navigation.getPageInfo('/patients');
```

### Navigation Menu Generation

```javascript
// Generate navigation menu HTML
const menuHTML = await navigation.generateNavigationHTML();
document.getElementById('nav-menu').innerHTML = menuHTML;

// Get navigation menu data
const menu = await navigation.generateNavigationMenu();
```

### Breadcrumb Generation

```javascript
// Generate breadcrumb HTML
const breadcrumbHTML = await navigation.generateBreadcrumbHTML();
document.getElementById('breadcrumb').innerHTML = breadcrumbHTML;

// Get breadcrumb data
const breadcrumb = await navigation.getBreadcrumb();
```

### Creating Navigation Links

```javascript
// Create a navigation link
const link = navigation.createNavLink('/patients', 'Patients', {
    className: 'nav-link',
    active: true
});
```

## HTML Integration

### Basic Navigation Links

```html
<!-- Use data-route attribute for automatic navigation -->
<a href="#" data-route="/patients">Patients</a>
<a href="#" data-route="/doctors">Doctors</a>
<a href="#" data-route="/appointments">Appointments</a>
```

### Navigation Menu

```html
<div id="navigation-menu"></div>
<script>
    // Load navigation menu
    navigation.generateNavigationHTML().then(html => {
        document.getElementById('navigation-menu').innerHTML = html;
    });
</script>
```

### Breadcrumb Navigation

```html
<div id="breadcrumb"></div>
<script>
    // Load breadcrumb
    navigation.generateBreadcrumbHTML().then(html => {
        document.getElementById('breadcrumb').innerHTML = html;
    });
</script>
```

## Adding New Routes

### 1. Add to Backend

Edit `backend/html_routes.py` and add your route to the appropriate category:

```python
"your_category": {
    "name": "Your Category",
    "pages": [
        {
            "route": "/your-route",
            "file": "your-page.html",
            "title": "Your Page Title",
            "description": "Your page description"
        }
    ]
}
```

### 2. Create HTML File

Create the corresponding HTML file in the `front_end` directory.

### 3. Test the Route

Visit `/app/your-route` to test your new route.

## Error Handling

The system includes comprehensive error handling:

- **404 errors** - Route not found
- **500 errors** - Server errors
- **Validation errors** - Invalid route parameters

Error pages are automatically served from:
- `error-404.html` for 404 errors
- `error-500.html` for 500 errors

## Testing the System

### 1. Start the Server

```bash
python run_server.py
```

### 2. Visit the Demo Page

Navigate to `http://127.0.0.1:8000/app/route-demo.html` to see the routing system in action.

### 3. Test Navigation

Use the demo page to:
- View all available routes
- Test route navigation
- Generate breadcrumbs
- Create navigation menus

## Best Practices

### 1. Route Naming
- Use descriptive, hierarchical routes
- Follow RESTful conventions
- Use kebab-case for multi-word routes

### 2. Page Organization
- Group related pages in categories
- Use consistent naming patterns
- Provide meaningful descriptions

### 3. Navigation UX
- Always provide breadcrumbs
- Use consistent navigation patterns
- Include loading states for dynamic content

### 4. Error Handling
- Provide fallback pages
- Show meaningful error messages
- Log errors for debugging

## Troubleshooting

### Common Issues

1. **Route not found**
   - Check if the route is defined in `html_routes.py`
   - Verify the HTML file exists
   - Check the file path in the route definition

2. **Navigation not working**
   - Ensure `navigation.js` is loaded
   - Check browser console for errors
   - Verify the navigation helper is initialized

3. **Breadcrumb not showing**
   - Check if the current route is valid
   - Verify the page info is available
   - Check for JavaScript errors

### Debug Mode

Enable debug mode by adding to your HTML:

```html
<script>
    // Enable debug logging
    window.navigation.debug = true;
</script>
```

## Future Enhancements

Potential improvements to the routing system:

1. **Route Guards** - Authentication and authorization
2. **Route Parameters** - Dynamic route parameters
3. **Route History** - Navigation history management
4. **Route Preloading** - Preload pages for better performance
5. **Route Analytics** - Track navigation patterns

## Conclusion

The HTML routing system provides a robust foundation for navigation in the Cabinet Management application. It offers organized route management, dynamic navigation, and comprehensive error handling while maintaining simplicity and ease of use.

For questions or issues, refer to the demo page at `/app/route-demo.html` or check the browser console for error messages.
