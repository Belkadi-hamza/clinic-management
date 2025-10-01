if($('#calendar').length > 0) {
    document.addEventListener('DOMContentLoaded', function() {
        var Draggable = FullCalendar.Draggable;

        // Initialize external events (the draggable ones)
        var containerEl = document.getElementById('external-events');
        new Draggable(containerEl, {
            itemSelector: '.fc-event',

            eventData: function (eventEl) {
                var className = eventEl.getAttribute('data-event-classname'); // Get the class name
                return {
                    title: eventEl.innerText.trim(),
                    classNames: [className], // Pass dynamic class name
                };
            }
        });
        
        var calendarEl = document.getElementById('calendar');       
        var calendar = new FullCalendar.Calendar(calendarEl, {
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
          initialView: 'dayGridMonth',
          eventDisplay: 'block',
          views: {
            dayGridMonth: {
              eventDisplay: 'block',
              dayMaxEvents: true
            }
          },
          eventDidMount: function(info) {
            // Ensure events show only title in month view
            if (info.view.type === 'dayGridMonth') {
              // Remove any time-related elements
              var eventEl = info.el;
              var timeElements = eventEl.querySelectorAll('.fc-event-time');
              timeElements.forEach(function(el) {
                el.style.display = 'none';
              });
              
              // Ensure only title is shown
              var titleEl = eventEl.querySelector('.fc-event-title');
              if (titleEl) {
                titleEl.style.fontWeight = 'normal';
              }
            }
          },
          events: [
            {
              title: 'Meeting',
              className: 'badge badge-info',
              backgroundColor: '#1976d2',
              textColor: "#fff",        
              start: new Date($.now() - 168000000).toISOString(),
              allDay: true
            },
            {
                title: 'Office',    
                className: 'badge badge-secondary',
                backgroundColor: '#0D7858' ,
                textColor: "#fff",                
                start: new Date($.now() + 338000000).toISOString(),
                allDay: true
            },
            {
                title: 'Hiring',
                className: 'badge badge-success',
                backgroundColor: '#09800F',     
                textColor: "#fff",        
                start: new Date($.now() - 338000000).toISOString(),
                allDay: true
            },
            {
                title: 'Holiday',
                className: 'badge badge-pink',
                backgroundColor: '#CC25B0',     
                textColor: "#fff",                
                start: new Date($.now() + 68000000).toISOString(),
                allDay: true
            },
            {
                title: 'Employee',
                className: 'badge badge-warning',
                backgroundColor: '#FDAF22', 
                textColor: "#fff",                
                start: new Date($.now() + 88000000).toISOString(),
                allDay: true
            }
          ],
          headerToolbar: {
            start: 'today prev,next',
            end: 'dayGridMonth,timeGridWeek,timeGridDay',
            center: 'title'
          }, 
          eventClick: function(info) {
            // Open modal
            $('#event_modal').modal('show');
            
            // Populate modal with event details
            document.getElementById('eventTitle').innerText = info.event.title;
          },
          dateClick: function(info) {
            // Only show modal if clicking on empty space, not on events
            if (info.dayEl && !info.dayEl.querySelector('.fc-event')) {
              // Show add new event modal when clicking on empty dates
              $('#add_new').modal('show');
              
              // Optionally, you can populate the modal with the clicked date
              // You might want to add a hidden input field in your modal to store the selected date
              if (info.date) {
                var selectedDate = info.date.toISOString().slice(0, 10); // Format as YYYY-MM-DD
                // If you have a date input in your modal, you can set it here
                // $('#event-date').val(selectedDate);
              }
            }
          },
          editable: true,
            droppable: true, // Enable drag and drop
            drop: function (info) {
                // If the event is dropped, do something here (optional)
                console.log('Event dropped');
            },
            eventReceive: function(info) {
                // When event is dropped on calendar
                console.log('Event added', info.event.title);
            }
        });     
        calendar.render();
    });         
}



if($('#calendar1').length > 0) {

    document.addEventListener('DOMContentLoaded', function() {
        var todayDate = moment().startOf('day');
        var YM = todayDate.format('YYYY-MM');
        var YESTERDAY = todayDate.clone().subtract(1, 'day').format('YYYY-MM-DD');
        var TODAY = todayDate.format('YYYY-MM-DD');
        var TOMORROW = todayDate.clone().add(1, 'day').format('YYYY-MM-DD');

        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, {
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
            },

            height: 500,
            contentHeight: 580,
            aspectRatio: 3,  // see: https://fullcalendar.io/docs/aspectRatio


            views: {
                dayGridMonth: { buttonText: 'month' },
                timeGridWeek: { buttonText: 'week' },
                timeGridDay: { buttonText: 'day' }
            },

            initialView: 'dayGridMonth',
            initialDate: TODAY,

            editable: true,
            dayMaxEvents: true, // allow "more" link when too many events
            navLinks: true,
            events: [
                {
                    title: 'All Day Event',
                    start: new Date($.now() - 168000000).toISOString(),
                    backgroundColor: '#FDE9ED',
                    allDay: true
                },
                {
                    id: 1000,
                    title: 'Repeating Event',
                    start: new Date($.now() - 338000000).toISOString(),
                    allDay: true
                }
            ]
        });

        calendar.render();
    });
}