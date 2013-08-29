// Foundation
jQuery(document).foundation();

// Problem tags autocomplete
jQuery('.problem-tag-select .text').autocomplete({
    minLength: 2,
    source: '/ajax/',
    messages: {
        noResults: '',
        results: function() {}
    },
    response: function(event, ui) {
        if (ui.content.length <= 0)
            return;
        output = '';
        for (i in ui.content) {
            item = ui.content[i];
            output += '<li class="problem-tag-item">'
                + '<a href="javascript:void(0);" contenteditable="false" class="button small" data-id="' + item.id + '"><i class="foundicon-plus"></i> ' + item.label + '</a>'
                + '<span class="description">' + item.description + '</span>'
                + '</li>';
        }
        result = jQuery('.problem-tag-result');
        result.html(output);
        if (result.css('display') == 'none') {
            result.fadeIn(200);
        }
        jQuery('.ui-front,.ui-helper-hidden-accessible').remove();

        // Problem tags select
        jQuery('.problem-tag-item').on('click', 'a.button', function(){
            id = jQuery(this).data('id');
            if (jQuery('.problem-tag-select .button[data-id="' + id + '"]').length > 0)
                return;

            tag = jQuery('.problem-tag');
            select = jQuery('.problem-tag-select');

            // Add tag and input data
            button = jQuery(this).clone();
            button.html(button.html().replace(/foundicon-plus/, 'foundicon-remove'));
            select.append(button);
            tag.append('<input type="hidden" name="tag" value="' + id + '">');

            // Clear text
            select.find('.text').html('');
            select.find('.text').remove().insertAfter(select.find('.button:last'));
        });
    }

});

// Remove tag and input data
jQuery('.problem-tag-select').on('click', 'a.button', function(){
    id = jQuery(this).remove().data('id');
    console.log(id);
    jQuery('.problem-tag input').filter('[name=tag]').filter('[value="' + id + '"]').remove();
});

// Focus writable area to simulate an input box
jQuery('.problem-tag-select').click(function(){
    jQuery(this).find('.text').focus();
});

// Show advanced options
jQuery('.problem-edit fieldset:nth-child(3)').hide();
jQuery('#advanced').click(function(){
    jQuery('.problem-edit fieldset:nth-child(3)').slideDown(300);
});
