(function () {
    "use strict";
    
    // Chat user list functionality
    $('.user-list').on('click', function() {
        $('.user-list').removeClass('active');
        $(this).addClass('active');
        
        // Update chat header with selected user info
        const userName = $(this).find('h6 a').text();
        const userAvatar = $(this).find('.avatar img').attr('src');
        
        $('.chat-messages .card-header .avatar img').attr('src', userAvatar);
        $('.chat-messages .card-header h6').text(userName);
        
        // Show chat messages area on mobile
        if ($(window).width() < 992) {
            $('.chat-messages').addClass('show');
            $('.chat-user-nav').addClass('hide');
        }
    });

    // Close chat on mobile
    $('.close-chat').on('click', function() {
        $('.chat-messages').removeClass('show');
        $('.chat-user-nav').removeClass('hide');
    });

    // Send message functionality
    $('.message-footer .form-control').on('keypress', function(e) {
        if (e.which === 13 && $(this).val().trim() !== '') {
            sendMessage();
        }
    });

    $('.message-footer .btn-primary').on('click', function() {
        if ($('.message-footer .form-control').val().trim() !== '') {
            sendMessage();
        }
    });

    function sendMessage() {
        const messageText = $('.message-footer .form-control').val().trim();
        const currentTime = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        const messageHTML = `
            <div class="chat-list ms-auto mb-3">
                <div class="d-flex align-items-start justify-content-end">
                    <div>
                        <div class="d-flex align-items-center justify-content-end mb-1">
                            <p class="mb-0 d-inline-flex align-items-center"><i class="ti ti-check text-light me-1"></i>${currentTime}<i class="ti ti-point-filled mx-2"></i></p>
                            <h6 class="fs-14 fw-semibold mb-0">You</h6>
                        </div>
                        <div class="d-flex align-items-center">
                            <div class="me-2">
                                <a href="javascript:void(0);" data-bs-toggle="dropdown"><i class="ti ti-dots-vertical"></i></a>
                                <ul class="dropdown-menu p-2">
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-arrow-back-up me-1"></i>Reply</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-arrow-forward-up me-1"></i>Forward</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-file-export me-1"></i>Copy</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-heart me-1"></i>Mark as Favourite</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-trash me-1"></i>Delete</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-check me-1"></i>Mark as Unread</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-box-align-right me-1"></i>Archeive Chat</a></li>
                                    <li><a class="dropdown-item" href="#"><i class="ti ti-pinned me-1"></i>Pin Chat</a></li>
                                </ul>
                            </div>
                            <div class="message-box sent-message p-3">
                                <p class="mb-0 fs-14">${messageText}</p>
                            </div>
                        </div>
                    </div>
                    <span class="avatar ms-2 online flex-shrink-0"><img src="assets/img/avatars/avatar-57.jpg" alt="user"></span>
                </div>
            </div>
        `;
        
        $('.message-body').append(messageHTML);
        $('.message-footer .form-control').val('');
        
        // Scroll to bottom
        $('.message-body').scrollTop($('.message-body')[0].scrollHeight);
        
        // Update message status after a delay
        setTimeout(function() {
            $('.message-body .chat-list:last-child .ti-check').removeClass('text-light').addClass('text-success');
        }, 1000);
    }

    // Search functionality
    $('.chat-user-nav .form-control').on('keyup', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.user-list').each(function() {
            const userName = $(this).find('h6 a').text().toLowerCase();
            const userMessage = $(this).find('p').text().toLowerCase();
            
            if (userName.includes(searchTerm) || userMessage.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    // Notification functionality
    $('.notification-read').on('click', function() {
        $(this).removeClass('bg-danger').addClass('bg-success');
        $(this).attr('data-bs-original-title', 'Marked as Read');
    });

    $('[data-dismissible]').on('click', function() {
        const notificationId = $(this).attr('data-dismissible');
        $(notificationId).fadeOut();
    });

    // Theme toggle
    $('#light-dark-mode').on('click', function() {
        const icon = $(this).find('i');
        if (icon.hasClass('ti-moon')) {
            icon.removeClass('ti-moon').addClass('ti-sun');
            $('body').addClass('dark-mode');
        } else {
            icon.removeClass('ti-sun').addClass('ti-moon');
            $('body').removeClass('dark-mode');
        }
    });

    // Sidebar toggle
    $('#toggle_btn, #toggle_btn2').on('click', function() {
        $('.sidebar').toggleClass('collapsed');
        $('.main-wrapper').toggleClass('sidebar-collapsed');
    });

    // Mobile sidebar
    $('#mobile_btn').on('click', function() {
        $('.sidebar').addClass('show');
    });

    $('.sidebar-close').on('click', function() {
        $('.sidebar').removeClass('show');
    });

    // Fullscreen functionality
    $('.btnFullscreen').on('click', function() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });

    // Auto-scroll to bottom of chat on load
    $(document).ready(function() {
        $('.message-body').scrollTop($('.message-body')[0].scrollHeight);
    });

})();
