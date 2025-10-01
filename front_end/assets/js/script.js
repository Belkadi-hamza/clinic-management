/*
Author       : Dreamstechnologies
Template Name: Dreams EMR - Bootstrap Admin Template
*/

(function () {
	"use strict";

	const $wrapper = $('.main-wrapper');
	const $overlay = $('<div class="sidebar-overlay"></div>');
	$overlay.insertBefore('.main-wrapper');

	// Toggle Mobile Menu
	$(document).on('click', '#mobile_btn', function (e) {
		e.preventDefault();
		$wrapper.toggleClass('slide-nav');
		$overlay.toggleClass('opened');
		$('html').toggleClass('menu-opened');
	});

	// Close sidebar on close button click
	$(document).on('click', '.sidebar-close, .sidebar-overlay', function () {
		$wrapper.removeClass('slide-nav');
		$overlay.removeClass('opened');
		$('html').removeClass('menu-opened');
	});

	// Sidebar
	function initSidebarMenu() {
		const $menuLinks = $('.sidebar-menu a');

		$menuLinks.on('click', function (e) {
			const $link = $(this);
			const $submenu = $link.next('ul');

			if ($link.parent().hasClass('submenu')) {
				e.preventDefault();

				if (!$link.hasClass('subdrop')) {
					// Collapse all other open submenus
					$link.closest('ul').find('ul:visible').slideUp(250);
					$link.closest('ul').find('a.subdrop').removeClass('subdrop');

					// Expand current
					$submenu.stop(true, true).slideDown(350);
					$link.addClass('subdrop');
				} else {
					// Collapse current
					$link.removeClass('subdrop');
					$submenu.stop(true, true).slideUp(350);
				}
			}
		});

		// Ensure any active link's submenu is shown with animation-ready state
		$('.sidebar-menu ul li.submenu a.active').each(function () {
			const $submenu = $(this).closest('ul');
			const $parentLink = $submenu.prev('a');

			$parentLink.addClass('active subdrop');
			$submenu.css('display', 'block'); // force show without using .show()

			// Now mark it manually as ready for animation
			$submenu.height($submenu.height()); // set explicit height
			$submenu.css('height', 'auto');     // restore auto height
		});
	}

	// Initialize Sidebar
	initSidebarMenu();


	// Mouse Over
	$(document).on('mouseover', function (e) {
		e.stopPropagation();
		if ($('body').hasClass('mini-sidebar') && $('#toggle_btn').is(':visible')) {
			var targ = $(e.target).closest('.sidebar, .header-left').length;
			if (targ) {
				$('body').addClass('expand-menu');
				$('.subdrop + ul').slideDown();
			} else {
				$('body').removeClass('expand-menu');
				$('.subdrop + ul').slideUp();
			}
			return false;
		}
	});

	// Toggle Button
	$(document).on('click', '#toggle_btn, #toggle_btn2', function () {
		const $body = $('body');
		const $html = $('html');
		const isMini = $body.hasClass('mini-sidebar');
		const isFullWidth = $html.attr('data-layout') === 'full-width';
		const isHidden = $html.attr('data-layout') === 'hidden';

		if (isMini) {
			$body.removeClass('mini-sidebar');
			$(this).addClass('active');
			localStorage.setItem('screenModeNightTokenState', 'night');
			setTimeout(function () {
				$(".header-left").addClass("active");
			}, 100);
		} else {
			$body.addClass('mini-sidebar');
			$(this).removeClass('active');
			localStorage.removeItem('screenModeNightTokenState');
			setTimeout(function () {
				$(".header-left").removeClass("active");
			}, 100);
		}

		// If <html> has data-layout="full-width", apply full-width class to <body>
		if (isFullWidth) {
			$body.addClass('full-width').removeClass('mini-sidebar');
			$('.sidebar-overlay').addClass('opened');
			$(document).on('click', '.sidebar-close', function () {
				$('body').removeClass('full-width');
			});
		} else {
			$body.removeClass('full-width');
		}

		// If <html> has data-layout="hidden", apply hidden-layout class to <body>
		if (isHidden) {
			$body.toggleClass('hidden-layout');
			$body.removeClass('mini-sidebar');
			$(document).on('click', '.sidebar-close', function () {
				$('body').removeClass('full-width');
			});
		}

		return false;
	});

	// Tooltip
	const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
	const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

	// Input Mask
	document.querySelectorAll('[data-toggle="input-mask"]').forEach(input => {
		const format = input.getAttribute('data-mask-format');
		const reverse = input.getAttribute('data-reverse') === 'true';
		if (format && typeof Inputmask !== 'undefined') {
			Inputmask({
				mask: format.replace(/0/g, '9'),
				reverse: reverse
			}).mask(input);
		}
	});

	// Form Validation
	document.querySelectorAll('.needs-validation').forEach(form => {
		form.addEventListener('submit', event => {
			if (!form.checkValidity()) {
				event.preventDefault();
				event.stopPropagation();
			}
			form.classList.add('was-validated');
		}, false);
	});

	// Initialize Flatpickr on elements with data-provider="flatpickr"
	document.querySelectorAll('[data-provider="flatpickr"]').forEach(el => {
		const config = {
			disableMobile: true
		};
		if (el.hasAttribute('data-date-format')) {
			config.dateFormat = el.getAttribute('data-date-format');
		}
		if (el.hasAttribute('data-enable-time')) {
			config.enableTime = true;
			config.dateFormat = config.dateFormat ? `${config.dateFormat} H:i` : 'Y-m-d H:i';
		}
		if (el.hasAttribute('data-altFormat')) {
			config.altInput = true;
			config.altFormat = el.getAttribute('data-altFormat');
		}
		if (el.hasAttribute('data-minDate')) {
			config.minDate = el.getAttribute('data-minDate');
		}
		if (el.hasAttribute('data-maxDate')) {
			config.maxDate = el.getAttribute('data-maxDate');
		}
		if (el.hasAttribute('data-default-date')) {
			const val = el.getAttribute('data-default-date');
			if (val && val !== 'true') config.defaultDate = val;
		}
		if (el.hasAttribute('data-multiple-date')) {
			config.mode = 'multiple';
		}
		if (el.hasAttribute('data-range-date')) {
			config.mode = 'range';
		}
		if (el.hasAttribute('data-inline-date')) {
			config.inline = true;
			const val = el.getAttribute('data-inline-date');
			if (val && val !== 'true') config.defaultDate = val;
		}
		if (el.hasAttribute('data-disable-date')) {
			config.disable = el.getAttribute('data-disable-date').split(',');
		}
		if (el.hasAttribute('data-week-number')) {
			config.weekNumbers = true;
		}
		flatpickr(el, config);
	});

	// Time Picker
	document.querySelectorAll('[data-provider="timepickr"]').forEach(item => {
		const attrs = item.attributes;
		const config = {
			enableTime: true,
			noCalendar: true,
			dateFormat: "H:i"
		};
		if (attrs["data-time-hrs"]) {
			config.time_24hr = true;
		}
		if (attrs["data-min-time"]) {
			config.minTime = attrs["data-min-time"].value;
		}
		if (attrs["data-max-time"]) {
			config.maxTime = attrs["data-max-time"].value;
		}
		if (attrs["data-default-time"]) {
			config.defaultDate = attrs["data-default-time"].value;
		}
		if (attrs["data-time-inline"]) {
			config.inline = true;
			config.defaultDate = attrs["data-time-inline"].value;
		}
		flatpickr(item, config);
	});

	// Select2
	if ($('[data-toggle="select2"]').length > 0) {
		$('[data-toggle="select2"]').each(function () {
			const $el = $(this);
			const options = {};
			// Placeholder
			if ($el.attr('data-placeholder')) {
				options.placeholder = $el.attr('data-placeholder');
			}

			// Allow clear
			if ($el.attr('data-allow-clear') === 'true') {
				options.allowClear = true;
			}

			// Tags input (user can enter new values)
			if ($el.attr('data-tags') === 'true') {
				options.tags = true;
			}

			// Maximum selection
			if ($el.attr('data-max-selections')) {
				options.maximumSelectionLength = parseInt($el.attr('data-max-selections'));
			}

			// AJAX (for dynamic search)
			if ($el.attr('data-ajax--url')) {
				options.ajax = {
					url: $el.attr('data-ajax--url'),
					dataType: 'json',
					delay: 250,
					data: function (params) {
						return {
							q: params.term, // search term
							page: params.page || 1
						};
					},
					processResults: function (data, params) {
						params.page = params.page || 1;
						return {
							results: data.items || [],
							pagination: {
								more: data.more
							}
						};
					},
					cache: true
				};
			}

			// Init Select2 with options
			$el.select2(options);
		});
	}

	// Select 2    
	if ($('.select').length > 0) {
		$('.select').select2({
			minimumResultsForSearch: -1,
			width: '100%'
		});
	}

	// Popover
	const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
	const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))

	// Toasts
	document.addEventListener('DOMContentLoaded', function () {
		const toastPlacement = document.getElementById('toastPlacement');
		const placementSelect = document.getElementById('selectToastPlacement');
		if (toastPlacement && placementSelect) {
			const originalClass = toastPlacement.className;
			placementSelect.addEventListener('change', function () {
				toastPlacement.className = `${originalClass} ${this.value}`.trim();
			});
		}
	});

	// Datatable
	if ($('.datatable').length > 0) {
		$('.datatable').DataTable({
			"bFilter": true,
			"sDom": 'fBtlpi',
			"ordering": true,
			"language": {
				search: ' ',
				searchPlaceholder: "Search",
				sLengthMenu: 'Showing _MENU_ Results',
				info: "_START_ - _END_ of _TOTAL_ items",
				paginate: {
					next: 'Next',
					previous: 'Prev'
				},
			},
			"responsive": true,
			"autoWidth": false,
			initComplete: (settings, json) => {
				$('.dataTables_filter').appendTo('#tableSearch');
				$('.dataTables_filter').appendTo('.search-input');
			},
		});
	}

	// Select Table Checkbox
	document.getElementById('select-all')?.addEventListener('change', function () {
		document.querySelectorAll('.form-check.form-check-md input[type="checkbox"]').forEach(function (checkbox) {
			checkbox.checked = this.checked;
		}, this);
	});

	// Full Screen
	if (document.querySelector('.btnFullscreen')) {
		const toggleFullscreen = function () {
			if (!document.fullscreenElement) {
				document.documentElement.requestFullscreen();
			} else {
				if (document.exitFullscreen) {
					document.exitFullscreen();
				}
			}
		};
		document.querySelectorAll('.btnFullscreen').forEach(function (btn) {
			btn.addEventListener('click', toggleFullscreen);
		});
	}

	// Sticky Sidebar
	if ($(window).width() > 767) {
		if ($('.theiaStickySidebar').length > 0) {
			$('.theiaStickySidebar').theiaStickySidebar({
				additionalMarginTop: 20
			});
		}
	}

	// Select
	function initCheckboxGroup(groupClass, selectAllClass, checkboxClass) {
		document.querySelectorAll('.' + groupClass).forEach(function (group) {
			const selectAll = group.querySelector('.' + selectAllClass);
			const checkboxes = group.querySelectorAll('.' + checkboxClass);

			if (selectAll) {
				selectAll.addEventListener('change', function () {
					checkboxes.forEach(function (checkbox) {
						checkbox.checked = selectAll.checked;
					});
				});
			}
		});
	}

	// Initialize all groups
	initCheckboxGroup('select-group', 'selectall', 'form-check-md');
	initCheckboxGroup('select-group2', 'selectall2', 'form-check-md2');
	initCheckboxGroup('select-group3', 'selectall3', 'form-check-md3');

	// Circle Progress
	document.querySelectorAll('.circle-progress').forEach(function (circle) {
		var value = parseFloat(circle.getAttribute('data-value'));
		var left = circle.querySelector('.progress-left .progress-bar');
		var right = circle.querySelector('.progress-right .progress-bar');

		if (value <= 0) {
			right.style.transform = 'rotate(0deg)';
			left.style.transform = 'rotate(0deg)';
		} else if (value <= 50) {
			right.style.transform = 'rotate(' + (value / 100 * 360) + 'deg)';
			left.style.transform = 'rotate(0deg)';
		} else if (value < 100) {
			right.style.transform = 'rotate(180deg)';
			left.style.transform = 'rotate(' + ((value - 50) / 100 * 360) + 'deg)';
		} else {
			// 100%: both halves at 180deg
			right.style.transform = 'rotate(180deg)';
			left.style.transform = 'rotate(180deg)';
		}
	});

	// Toggle Password
	document.querySelectorAll('.toggle-password').forEach(function (toggle) {
		toggle.addEventListener('click', function () {
			const icon = this.querySelector('i');
			const input = this.closest('.input-group').querySelector('.pass-input');
			if (input.getAttribute('type') === 'password') {
				input.setAttribute('type', 'text');
				icon.classList.remove('ti-eye-off');
				icon.classList.add('ti-eye');
			} else {
				input.setAttribute('type', 'password');
				icon.classList.remove('ti-eye');
				icon.classList.add('ti-eye-off');
			}
		});
	});

	//Increment Decrement Numberes
	document.addEventListener("DOMContentLoaded", function () {
		document.querySelectorAll(".custom-increment.cart").forEach(container => {
			const input = container.querySelector("input[type='text']");

			const incrementBtn = container.querySelector("button[class*='increment']");
			const decrementBtn = container.querySelector("button[class*='decrement']");

			if (!input || !incrementBtn || !decrementBtn) return;

			incrementBtn.addEventListener("click", function () {
				let current = parseInt(input.value, 10) || 0;
				input.value = current + 1;
			});

			decrementBtn.addEventListener("click", function () {
				let current = parseInt(input.value, 10) || 0;
				input.value = Math.max(0, current - 1); // Prevent going below 0
			});
		});
	});

	// Add Patient
	if (document.querySelector('.vertical-tab')) {
		// Next button
		document.querySelectorAll('.form-wizard-content .next-tab-btn').forEach(btn => {
			btn.addEventListener('click', function () {
				const fieldset = this.closest('.form-wizard-content');
				const nextFieldset = fieldset?.nextElementSibling;
				const progressBar = document.querySelector('.vertical-tab .nav-pills');

				if (fieldset && nextFieldset && progressBar) {
					fieldset.classList.remove('active'); // Hide current step
					nextFieldset.classList.add('active'); // Show next step

					// Optional: fade effect
					nextFieldset.style.opacity = 0;
					nextFieldset.style.transition = 'opacity 0.5s';
					setTimeout(() => {
						nextFieldset.style.opacity = 1;
					}, 10);

					// Update progress bar state
					const active = progressBar.querySelector('.active');
					if (active) {
						active.classList.remove('active');
						active.classList.add('activated');
						const next = active.nextElementSibling;
						if (next) next.classList.add('active');
					}
				}
			});
		});

		// Back button
		document.querySelectorAll('.form-wizard-content .back-btn').forEach(btn => {
			btn.addEventListener('click', function () {
				const fieldset = this.closest('.form-wizard-content');
				const prevFieldset = fieldset?.previousElementSibling;
				const progressBar = document.querySelector('.vertical-tab .nav-pills');

				if (fieldset && prevFieldset && progressBar) {
					fieldset.classList.remove('active'); // Hide current step
					prevFieldset.classList.add('active'); // Show previous step

					// Optional: fade effect
					prevFieldset.style.opacity = 0;
					prevFieldset.style.transition = 'opacity 0.5s';
					setTimeout(() => {
						prevFieldset.style.opacity = 1;
					}, 10);

					// Update progress bar state
					const active = progressBar.querySelector('.active');
					if (active) {
						active.classList.remove('active', 'activated');
						const prev = active.previousElementSibling;
						if (prev) prev.classList.add('active');
					}
				}
			});
		});
	}

	// Date Range Picker
	if ($('#reportrange').length > 0) {
		const start = moment().subtract(0, "days");
		const end = moment();
		const report_range = (start, end) => {
			$("#reportrange span").html(`${start.format("D MMM YY")} - ${end.format("D MMM YY")}`);
		};
		$("#reportrange").daterangepicker(
			{
				startDate: start,
				endDate: end,
				ranges: {
					'Today': [moment(), moment()],
					'Yesterday': [moment().subtract(1, "days"), moment().subtract(1, "days")],
					"Last 7 Days": [moment().subtract(6, "days"), moment()],
					"Last 30 Days": [moment().subtract(29, "days"), moment()],
					"This Month": [moment().startOf("month"), moment().endOf("month")],
					"Last Month": [
						moment().subtract(1, "month").startOf("month"),
						moment().subtract(1, "month").endOf("month")
					]
				}
			},
			report_range
		);
		report_range(start, end);
	}

	// Mail Check
	document.addEventListener("DOMContentLoaded", function () {
		// Select all checkboxes inside the table
		const checkboxes = document.querySelectorAll(".mail-check-input");

		checkboxes.forEach((checkbox) => {
			checkbox.addEventListener("change", function () {
				const row = this.closest("tr"); // Find the closest <tr> parent
				if (this.checked) {
					row.classList.add("mail-selected"); // Add class when checked
				} else {
					row.classList.remove("mail-selected"); // Remove class when unchecked
				}
			});
		});
	});

	// Aprrearence Settings 
	document.querySelectorAll('.theme-image').forEach(function (img) {
		img.addEventListener('click', function () {
			document.querySelectorAll('.theme-image').forEach(function (el) {
				el.classList.remove('active');
			});
			this.classList.add('active');
		});
	});

	// Kanban Drag
	if ($('.kanban-drag-wrap').length > 0) {
		$(".kanban-drag-wrap").sortable({
			connectWith: ".kanban-drag-wrap",
			handle: ".kanban-card",
			placeholder: "drag-placeholder"
		});
	}

	// Click
	document.querySelectorAll('.star').forEach(function (star) {
		star.addEventListener('click', function (e) {
			e.preventDefault();
			e.stopPropagation();

			let icon = this.querySelector('i');
			icon.classList.toggle('ti-star');
			icon.classList.toggle('ti-star-filled');
			icon.classList.toggle('text-warning'); // Optional color change
		});
	});

	// Gallery
	if ($('.call-users').length > 0) {
		var swiper = new Swiper(".call-users", {
			slidesPerView: 1,
			spaceBetween: 24,
			keyboard: {
				enabled: true,
			},
			pagination: {
				el: ".swiper-pagination",
				clickable: true,
			},
			navigation: {
				nextEl: ".swiper-button-next",
				prevEl: ".swiper-button-prev",
			},
			loop: true,
			breakpoints: {
				320: {
					slidesPerView: 1,
				},
				576: {
					slidesPerView: 2,
				},
				768: {
					slidesPerView: 3,
				},
				992: {
					slidesPerView: 3,
				},
				1300: {
					slidesPerView: 4,
				},
			}
		});
	}

})();

$(document).ready(function () {
	$('.select').select2();
});