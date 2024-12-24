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

            // Initialize the inline formsets
            $('.inline-group').each(function() {
                $(this).find('input[name$="-TOTAL_FORMS"]').val('1');
                $(this).find('input[name$="-INITIAL_FORMS"]').val('0');
                $(this).find('input[name$="-MIN_NUM_FORMS"]').val('0');
                $(this).find('input[name$="-MAX_NUM_FORMS"]').val('1');
            });
        }

        // Update inlines when radio buttons change
        $('input[name="capture_type"]').change(updateInlines);
        
        // Initial update on page load
        updateInlines();
    });
})(django.jQuery);
