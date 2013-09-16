// Tag renderer

function tag_field(id, label, description) {
    return '<li class="problem-tag-item">'
        + '<a href="javascript:void(0);" contenteditable="false" class="button small" data-id="' + id + '"><i class="foundicon-plus"></i> ' + label + '</a>'
        + '<span class="description">' + description + '</span>'
        + '</li>';
}

// jQuery calls

jQuery.noConflict();
(function($){

// Foundation

$(document).foundation();

// Highlight

$.fn.highlight = function (color) {
    if (!color) color = '#80FF76';
    var e = $(this[0]);
    var original = e.css('backgroundColor');
    return e.animate({ backgroundColor: color }, 1000, null, function(){
        e.animate({ backgroundColor:original });
    });
};

// Problem tags autocomplete

$('.problem-tag-select .text').autocomplete({
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
            output += tag_field(0, $('.problem-tag-select .text').text(), '');
        }

        result = $('.problem-tag-result');
        result.html(output);
        if (result.css('display') == 'none') {
            result.fadeIn(200);
        }
        $('.ui-front,.ui-helper-hidden-accessible').remove();

        // Problem tags select
        $('.problem-tag-item').on('click', 'a.button', function(){
            id = $(this).data('id');
            if ($('.problem-tag-select .button[data-id="' + id + '"]').length > 0)
                return;

            tag = $('.problem-tag');
            select = $('.problem-tag-select');

            // Add tag and input data
            button = $(this).clone();
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

$('.problem-tag-select').on('click', 'a.button', function(){
    id = $(this).remove().data('id');
    console.log(id);
    $('.problem-tag input').filter('[name=tag]').filter('[value="' + id + '"]').remove();
});

// Focus writable area to simulate an input box

$('.problem-tag-select').click(function(){
    $(this).find('.text').focus();
});

// Show advanced options

$('.problem-edit fieldset:gt(0)').hide();
$('#advanced').click(function(){
    $('.problem-edit fieldset:gt(0)').each(function(){ $(this).fadeIn(300); });
});

// Revision rendering

$('.revisions').ready(function(){
    var raw = $('.raw');
    for (i=0; i < raw.length - 1; i++) {
        h1 = $(raw[i+1]).html();
        h2 = $(raw[i]).html();
        if (h1 == h2)
            continue;
        d = diff(h1, h2);
        $(raw[i]).next('.diff').html(d);
    }
    $(raw[raw.length-1]).next('.diff').html($(raw[raw.length-1]).html());
});

// Show on click

$('.show-on-click').click(function(){
    var id = $(this).data('show-on-click');
    $('#' + id).delay(300).fadeIn(300);
});

// Hide after click

$('.hide-after-click').click(function(){
    $(this).fadeOut(300);
});

// Select all on click

$('.select-on-click').click(function(){
    $(this).select();
});

// Idea form
// Not using 'show-on-click' because of the resizing problem

$('.problem-idea-form-button').click(function(){
    $(this).fadeOut(300);
    $('.problem-idea-form').delay(300).fadeIn(300);
    CKEDITOR.instances.id_content.resize('100', '340');
});

// Comment form submit

$('.comment-form form').submit(function(e){
    e.preventDefault();
    var idea = $(this).parent().data('idea');
    var comments = $('#comments-' + idea);
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: $(this).serialize(),
        complete: function(xhr, data) {
            if (data == 'success') {
                var c = comments.append(xhr.responseText);
                $('.comment-form').fadeOut(300);
                comments.find('.comment').last().highlight();
            }
        }
    });
});

// Voting

$('.voting a').click(function() {

    if ($(this).attr('disabled') || $(this).data('reveal-id').length)
        return;

    var action;
    var idea = $(this).data('idea');

    var upvoting = $(this).hasClass('upvote');
    var downvoting = $(this).hasClass('downvote');

    var upvote;
    if (upvoting)
        upvote = $(this);
    else
        upvote = $(this).siblings('.upvote');

    var downvote;
    if (downvoting)
        downvote = $(this);
    else
        downvote = $(this).siblings('.downvote');

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

    var counter = $(this).siblings('.vote-count');
    counter.html(parseInt(counter.text()) + sum);

    var weight;
    if (upvoting)
        weight = 1;
    else if (downvoting)
        weight = -1;

    $.ajax({
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

})(jQuery);
