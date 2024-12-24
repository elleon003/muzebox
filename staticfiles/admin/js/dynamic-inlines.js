(function($) {
    $(document).ready(function() {
        // Function to show/hide inlines based on capture type
        function updateInlines() {
            var selectedType = $('input[name="capture_type"]:checked').val();
            
            // Hide all inline groups first
            $('.inline-group').hide();
            
            // Show the appropriate inline group based on selection
            if (selectedType === 'TEXT') {
                $('.inline-group:has([id^="textcapture"])').show();
            } else if (selectedType === 'AUDIO' || selectedType === 'VIDEO') {
                $('.inline-group:has([id^="mediacapture"])').show();
            }
        }

        // Update inlines when radio buttons change
        $('input[name="capture_type"]').change(updateInlines);
        
        // Initial update on page load
        updateInlines();
    });
})(django.jQuery);
