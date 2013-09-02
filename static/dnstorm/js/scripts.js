// Foundation
jQuery(document).foundation();

// Problem tags autocomplete

function tag_field(id, label, description) {
    return '<li class="problem-tag-item">'
        + '<a href="javascript:void(0);" contenteditable="false" class="button small" data-id="' + id + '"><i class="foundicon-plus"></i> ' + label + '</a>'
        + '<span class="description">' + description + '</span>'
        + '</li>';
}

jQuery('.problem-tag-select .text').autocomplete({
    minLength: 2,
    source: '/ajax/',
    messages: {
        noResults: '',
        results: function() {}
    },
    response: function(event, ui) {
        console.log(ui);
        output = '';
        if (ui.content.length > 0) {
            for (i in ui.content) {
                item = ui.content[i];
                output += tag_field(item.id, item.label, item.description)
            }
        } else {
            output += tag_field(0, jQuery('.problem-tag-select .text').text(), '');
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

jQuery('.problem-edit fieldset:gt(0)').hide();
jQuery('#advanced').click(function(){
    jQuery('.problem-edit fieldset:gt(0)').each(function(){ jQuery(this).fadeIn(300); });
});

// Revision rendering

jQuery('.revisions').ready(function(){
    var raw = jQuery('.raw');
    for (i=0; i < raw.length - 1; i++) {
        h1 = jQuery(raw[i+1]).html();
        h2 = jQuery(raw[i]).html();
        if (h1 == h2)
            continue;
        d = diff(h1, h2);
        jQuery(raw[i]).next('.diff').html(d);
    }
    jQuery(raw[raw.length-1]).next('.diff').html(jQuery(raw[raw.length-1]).html());
});

// Idea form

jQuery('.problem-idea-form-button').click(function(){
    jQuery(this).fadeOut();
    jQuery('.problem-idea-form').fadeIn();
    CKEDITOR.instances.id_content.resize('100', '340');
});

// Voting

jQuery('.voting a').click(function() {

    if (jQuery(this).attr('disabled') || jQuery(this).data('reveal-id').length)
        return;

    var action;
    var idea = jQuery(this).data('idea');

    var upvoting = jQuery(this).hasClass('upvote');
    var downvoting = jQuery(this).hasClass('downvote');

    var upvote;
    if (upvoting)
        upvote = jQuery(this);
    else
        upvote = jQuery(this).siblings('.upvote');

    var downvote;
    if (downvoting)
        downvote = jQuery(this);
    else
        downvote = jQuery(this).siblings('.downvote');

    var upvoted = upvote.hasClass('success');
    var downvoted = downvote.hasClass('alert');

    upvote.removeClass('success');
    downvote.removeClass('alert');

    var sum;
    if (upvoting && upvoted) {
        sum = -1;
    } else if (downvoting && downvoted) {
        sum = 1;
    } else if (upvoting && downvoted) {
        sum = 2;
        upvote.addClass('success');
    } else if (downvoting && upvoted) {
        sum = -2;
        downvote.addClass('alert');
    } else if (upvoting && !upvoted) {
        sum = 1;
        upvote.addClass('success');
    } else if (downvoting && !downvoted) {
        sum = -1;
        downvote.addClass('alert');
    }

    var counter = jQuery(this).siblings('.vote-count');
    counter.html(parseInt(counter.text()) + sum);

    var weight;
    if (upvoting)
        weight = 1;
    else if (downvoting)
        weight = -1;

    jQuery.ajax({
        url: '/ajax/',
        data: {
            'idea': idea,
            'weight': weight
        },
        complete: function(xhr, data) {
            count = parseInt(data);
            // Reset stuff if things go wrong
            if (isNaN(count)) {
                upvote.removeClass('success');
                downvote.removeClass('alert');
                counter.html(parseInt(counter.html()) - weight);
            }
            counter.html(count);
        }
    });

});
