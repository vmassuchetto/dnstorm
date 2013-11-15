jQuery.noConflict();
(function($){

// Cookies

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Foundation

$(document).foundation();

// Highlight

$.fn.highlight = function (color) {
    if (color == 'red')
        color = '#FF6666';
    else
        color = '#A8FFA2';
    var e = $(this[0]);
    var original = e.css('backgroundColor');
    return e.animate({ backgroundColor: color }, 1000, null, function(){
        e.animate({ backgroundColor:original });
    });
};

// Modal cancel button
// When we want to use a button instead of the "X" at the top

$('.close-reveal-modal-button').click(function(){
    $(this).parents('.reveal-modal').foundation('reveal', 'close');
});

// Criteria tag button renderer

function criteria_field(id, label, description) {
    return '<li class="problem-criteria-item">'
        + '<a href="javascript:void(0);" contenteditable="false" class="button small" data-id="' + id + '"><i class="foundicon-plus"></i> ' + label + '</a>'
        + '<span class="description">' + description + '</span>'
        + '</li>';
}

function criteria_add_button(button) {

    // Empty search input
    $('.problem-criteria-select .text').text('');

    // Create hidden field
    b = button.clone();
    b.html(b.html().replace(/foundicon-plus/, 'foundicon-remove'));
    $('.problem-criteria-select .text').before(b);
    $('.problem-form').append('<input type="hidden" name="criteria_' + b.data('id') + '" value="' + b.data('id') + '">');

}

// Problem criterias autocomplete

$('.problem-criteria-select .text').autocomplete({
    minLength: 2,
    source: '/ajax/',
    messages: {
        noResults: '',
        results: function() {}
    },
    response: function(event, ui) {
        output = '';
        if (ui.content.length > 0) {
            for (i in ui.content) {
                item = ui.content[i];
                output += criteria_field(item.id, item.label, item.description)
            }
        } else {
            output += criteria_field(0, $('.problem-criteria-select .text').text(), 'Click above to create this criteria.');
        }

        result = $('.problem-criteria-result');
        result.html(output);
        if (result.css('display') == 'none') {
            result.fadeIn(200);
        }
        $('.ui-front,.ui-helper-hidden-accessible').remove();

        // Problem criteria select
        $('.problem-criteria-item').on('click', 'a.button', function(){ 
            id = $(this).data('id');

            // Already selected
            if ($('.problem-criteria-select .button[data-id="' + id + '"]').length > 0)
                return;

            // Existing criteria, just append the button
            if (id != 0) {
                criteria_add_button($(this));

            // Otherwise, call the new criteria form
            } else {
                modal = $('#criteria-modal');
                modal.find('#id_name').val($('.problem-criteria-select .text').text());
                modal.foundation('reveal', 'open');
            }

        });
    }
});

// Criteria modal form

$('#criteria-modal form').submit(function(e){
    e.preventDefault();
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        dataType: 'json',
        data: $(this).serialize(),
        success: function(data) {

            // Clear and hide form for future use
            modal.foundation('reveal', 'close');
            modal.find('#id_name').val('');
            modal.find('#criteria_description').val('');

            // Insert button
            button = $('.problem-criteria-result li a[data-id="0"]');
            button.data('id', data.id);
            button.attr('data-id', data.id);
            button.siblings('.description').text(data.description);
            criteria_add_button(button);

        }
    });
});

// Remove criteria and input data

$('.problem-criteria-select').on('click', 'a.button', function(){
    id = $(this).remove().data('id');
    $('.problem-form input').filter(function() { return this.name.match(/^criteria_[0-9]+$/); }).filter('[value="' + id + '"]').remove();
    $('.tooltip').fadeOut();
});

// Focus writable area to simulate an input box

$('.problem-criteria-select').click(function(){
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

// Show idea form
// Not using 'show-on-click' because of the resizing problem

$('.problem-idea-form-button').click(function(){
    $('.problem-idea-button').fadeOut(300);
    CKEDITOR.instances.id_content.resize('100', '340');
    $('.problem-idea-form').delay(300).fadeIn(300);
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

// Comment delete

$('.comment-delete').click(function(){
    var c = $(this).parent();
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            delete_comment: $(this).data('comment')
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                c.highlight('red');
                c.fadeOut(300);
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


// Table section

var table = $('.problem-table');
var alternative_add_modal = $('#alternative-add-modal');

// Table overflow adjust

function adjust_table_overflow() {
    if ($('.problem-table-wrap').lenght <= 0 || !table)
        return;
    if (table.width() > $('.problem-table-wrap').width())
        $('.problem-table-wrap').css('overflow-x', 'scroll');
}

adjust_table_overflow();

// New criteria

/*$('.add-criteria').click(function(){
    alternative_modal.find('input#id_title').val('');
    alternative_modal.find('textarea#id_description').val('');
    alternative_modal.find('input#id_mode').val('criteria');
    alternative_modal.find('input#id_object').val('new');
    alternative_modal.foundation('reveal', 'open');
});*/

// New alternative

$('.add-alternative').click(function(){
    alternative_add_modal.find('input#id_title').val('');
    alternative_add_modal.find('textarea#id_description').val('');
    alternative_add_modal.find('input#id_mode').val('alternative');
    alternative_add_modal.find('input#id_object').val('new');
    alternative_add_modal.foundation('reveal', 'open');
});

// Table title modal submit

$('#alternative-add-modal form').submit(function(e){
    e.preventDefault();
    var form = $(this);

    // New alternative

    if ('new' == form.find('input[name="object"]').val()
        && 'alternative' == form.find('input[name="mode"]').val()) {
        $.ajax({
            url: '/ajax/',
            type: 'POST',
            data: form.serialize(),
            complete: function(xhr, data) {
                alternative = $.parseJSON(xhr.responseText);
                if (isNaN(alternative.id))
                    return;
                new_alternative = '<tr class="alternative" id="alternative-' + alternative.id + '" data-alternative="' + alternative.id + '">'
                    + '<td class="vertical-title">'
                    + '<span data-tooltip title="' + alternative.description + '">' + alternative.title + '</span>'
                    + '&nbsp;<a class="foundicon-edit edit-table-title" data-reveal-id="alternative-edit-modal"></a>'
                    + '&nbsp;<a class="foundicon-remove" data-reveal-id="alternative-remove-modal"></a>'
                    + '</td>';
                n_criteria = table.find('th.criteria').length;
                for (i = 0; i < n_criteria; i++) {
                    new_alternative += '<td><a class="button expand secondary select-idea">' + gettext('Select idea') + '</a></td>';
                }
                new_alternative += '</tr>';
                table.find('tbody').append(new_alternative);
                adjust_table_overflow();
                alternative_add_modal.foundation('reveal', 'close');
                table.find('#alternative-' + alternative.id).highlight();
            }
        });
    }
});

$('.problem-idea').click(function(){
    var modal = $('#table-idea-modal');
    var criteria = modal.data('criteria');
    var alternative = modal.data('alternative');
    var idea = $(this).data('idea');
    var item_object = modal.data('item');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: {
            'criteria': criteria,
            'alternative': alternative,
            'idea': idea
        },
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        },
        complete: function(xhr, data) {
            item = $.parseJSON(xhr.responseText);
            if (isNaN(item.id))
                return;
            item_object.html('#' + item.id).highlight();
            modal.foundation('reveal', 'close');
        }
    });
});

// Select idea in the problem table

$(document.body).on('click', '.select-idea', function(){
    var modal = $('#table-idea-modal');
    modal.data('criteria', $(this).data('criteria'));
    modal.data('alternative', $(this).data('alternative'));
    modal.data('item', $(this).parent());
    modal.foundation('reveal', 'open');
});

})(jQuery);
