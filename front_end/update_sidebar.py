#!/usr/bin/env python3
"""
Script to update sidebar navigation in all HTML files
"""
import re
import os
from pathlib import Path

# The new sidebar HTML (without .html extensions)
NEW_SIDEBAR = '''        <div class="sidebar" id="sidebar">

            <!-- Start Logo -->
            <div class="sidebar-logo">
                <div>
                    <!-- Logo Normal -->
                    <a href="index" class="logo logo-normal">
                        <img src="assets/img/logo.svg" alt="Logo">
                    </a>

                    <!-- Logo Small -->
                    <a href="index" class="logo-small">
                        <img src="assets/img/logo-small.svg" alt="Logo">
                    </a>

                    <!-- Logo Dark -->
                    <a href="index" class="dark-logo">
                        <img src="assets/img/logo-dark.svg" alt="Logo">
                    </a>
                </div>
                <button class="sidenav-toggle-btn btn border-0 p-0 active" id="toggle_btn">
                    <i class="ti ti-arrow-bar-to-left"></i>
                </button>

                <!-- Sidebar Menu Close -->
                <button class="sidebar-close">
                    <i class="ti ti-x align-middle"></i>
                </button>
            </div>
            <!-- End Logo -->

            <!-- Sidenav Menu -->
            <div class="sidebar-inner" data-simplebar>
                <div id="sidebar-menu" class="sidebar-menu">
                    <ul role="menu" aria-label="Main navigation menu">
                        <li class="menu-title" aria-disabled="true"><span>MAIN</span></li>

                        <li>
                            <a href="index" {ACTIVE_INDEX}>
                                <i class="ti ti-layout-board"></i><span>Dashboard</span>
                            </a>
                        </li>

                        <li class="menu-title" aria-disabled="true"><span>HEALTHCARE</span></li>

                        <li>
                            <a href="patients" {ACTIVE_PATIENTS}>
                                <i class="ti ti-users"></i><span>Patients</span>
                            </a>
                        </li>

                        <li>
                            <a href="doctors" {ACTIVE_DOCTORS}>
                                <i class="ti ti-stethoscope"></i><span>Doctors</span>
                            </a>
                        </li>

                        <li>
                            <a href="appointments" {ACTIVE_APPOINTMENTS}>
                                <i class="ti ti-calendar-time"></i><span>Appointments</span>
                            </a>
                        </li>

                        <li>
                            <a href="visits" {ACTIVE_VISITS}>
                                <i class="ti ti-e-passport"></i><span>Visits</span>
                            </a>
                        </li>

                        <li class="submenu">
                            <a href="javascript:void(0);">
                                <i class="ti ti-test-pipe"></i><span>Laboratory</span><span class="menu-arrow"></span>
                            </a>
                            <ul>
                                <li>
                                    <a href="lab-results" {ACTIVE_LAB}>Lab Results</a>
                                </li>
                                <li>
                                    <a href="medical-results" {ACTIVE_MEDICAL}>Medical Rsults</a>
                                </li>
                            </ul>
                        </li>

                        <li>
                            <a href="pharmacy" {ACTIVE_PHARMACY}>
                                <i class="ti ti-prescription"></i><span>Pharmacy</span>
                            </a>
                        </li>

                        <li class="menu-title" aria-disabled="true"><span>MANAGE</span></li>

                        <li>
                            <a href="staffs" {ACTIVE_STAFFS}>
                                <i class="ti ti-users-group"></i><span>Staffs</span>
                            </a>
                        </li>
                        <li>
                            <a href="roles" {ACTIVE_ROLES}>
                                <i class="ti ti-users-group"></i><span>Roles</span>
                            </a>
                        </li>

                    </ul>
                </div>
            </div>

        </div>'''

# Map file patterns to active menu items
ACTIVE_PATTERNS = {
    'index': 'ACTIVE_INDEX',
    'patient': 'ACTIVE_PATIENTS',
    'doctor': 'ACTIVE_DOCTORS',
    'appointment': 'ACTIVE_APPOINTMENTS',
    'visit': 'ACTIVE_VISITS',
    'lab-result': 'ACTIVE_LAB',
    'medical-result': 'ACTIVE_MEDICAL',
    'pharmacy': 'ACTIVE_PHARMACY',
    'staff': 'ACTIVE_STAFFS',
    'role': 'ACTIVE_ROLES',
}

def get_active_class(filename):
    """Determine which menu item should be active based on filename"""
    active_vars = {
        'ACTIVE_INDEX': '',
        'ACTIVE_PATIENTS': '',
        'ACTIVE_DOCTORS': '',
        'ACTIVE_APPOINTMENTS': '',
        'ACTIVE_VISITS': '',
        'ACTIVE_LAB': '',
        'ACTIVE_MEDICAL': '',
        'ACTIVE_PHARMACY': '',
        'ACTIVE_STAFFS': '',
        'ACTIVE_ROLES': '',
    }
    
    for pattern, var in ACTIVE_PATTERNS.items():
        if pattern in filename.lower():
            active_vars[var] = 'class="active"'
            break
    
    return active_vars

def update_sidebar_in_file(filepath):
    """Update the sidebar in a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has a sidebar
        if '<div class="sidebar" id="sidebar">' not in content:
            print(f"  ⊘ Skipping {filepath.name} (no sidebar found)")
            return False
        
        # Find the sidebar section
        pattern = r'<div class="sidebar" id="sidebar">.*?</div>\s*<!-- Sidenav Menu End -->'
        
        if not re.search(pattern, content, re.DOTALL):
            print(f"  ⚠ Warning: Could not find complete sidebar in {filepath.name}")
            return False
        
        # Get active class for this file
        filename = filepath.stem
        active_vars = get_active_class(filename)
        
        # Replace placeholders in new sidebar
        new_sidebar_content = NEW_SIDEBAR
        for var, value in active_vars.items():
            new_sidebar_content = new_sidebar_content.replace('{' + var + '}', value)
        
        # Add the closing comment
        new_sidebar_with_comment = new_sidebar_content + '\n        <!-- Sidenav Menu End -->'
        
        # Replace the old sidebar with new one
        new_content = re.sub(pattern, new_sidebar_with_comment, content, flags=re.DOTALL)
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ Updated {filepath.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error updating {filepath.name}: {e}")
        return False

def main():
    """Main function to update all HTML files"""
    script_dir = Path(__file__).parent
    html_files = list(script_dir.glob('*.html'))
    
    # Exclude certain files
    exclude_files = {'login.html', 'error-404.html', 'error-500.html', 'loading.html', 
                     'connection-refused.html', 'clean-urls-demo.html', 'redirect-test.html',
                     'route-demo.html', 'test-assets.html'}
    
    html_files = [f for f in html_files if f.name not in exclude_files]
    
    print(f"Found {len(html_files)} HTML files to update\n")
    
    updated_count = 0
    for html_file in sorted(html_files):
        if update_sidebar_in_file(html_file):
            updated_count += 1
    
    print(f"\n✓ Successfully updated {updated_count} out of {len(html_files)} files")

if __name__ == '__main__':
    main()
