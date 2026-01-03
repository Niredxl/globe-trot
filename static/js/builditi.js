 const sectionsContainer = document.getElementById('itinerary-sections');

    // Function to update stop numbering (Stop 1, Stop 2, etc.)
    function updateStopNumbers() {
        const stops = sectionsContainer.getElementsByClassName('itinerary-stop');
        Array.from(stops).forEach((stop, index) => {
            stop.querySelector('.stop-label').innerText = `Stop ${index + 1}: Destination Details`;
            
            // Hide remove button if only one stop remains
            const removeBtn = stop.querySelector('.remove-stop-btn');
            removeBtn.style.display = (stops.length === 1) ? 'none' : 'block';
        });
    }

    // Logic to add a new stop [cite: 22, 50]
    document.getElementById('add-stop-btn').addEventListener('click', function() {
        const firstStop = document.querySelector('.itinerary-stop');
        const newStop = firstStop.cloneNode(true);
        
        // Clear all inputs in the new card
        newStop.querySelectorAll('input, textarea').forEach(input => input.value = '');
        
        sectionsContainer.appendChild(newStop);
        updateStopNumbers();
    });

    // Logic to remove a stop using Event Delegation
    sectionsContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-stop-btn')) {
            const stopCard = e.target.closest('.itinerary-stop');
            stopCard.remove();
            updateStopNumbers();
        }
    });

    // Initialize display logic
    updateStopNumbers();