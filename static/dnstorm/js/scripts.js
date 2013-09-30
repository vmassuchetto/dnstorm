jQuery.noConflict();
(function($){

// Tag renderer

function tag_field(id, label, description) {
    return '<li class="problem-tag-item">'
        + '<a href="javascript:void(0);" contenteditable="false" class="button small" data-id="' + id + '"><i class="foundicon-plus"></i> ' + label + '</a>'
        + '<span class="description">' + description + '</span>'
        + '</li>';
}

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

// Problem tags autocomplete

$('.problem-tag-select .text').autocomplete({
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
var table_title_modal = $('#table-title-modal');

// Table overflow adjust

function adjust_table_overflow() {
    if ($('.problem-table-wrap').lenght <= 0 || !table)
        return;
    if (table.width() > $('.problem-table-wrap').width())
        $('.problem-table-wrap').css('overflow-x', 'scroll');
}

adjust_table_overflow();

// New criteria

$('.add-criteria').click(function(){
    table_title_modal.find('input#id_title').val('');
    table_title_modal.find('textarea#id_description').val('');
    table_title_modal.find('input#id_mode').val('criteria');
    table_title_modal.find('input#id_object').val('new');
    table_title_modal.foundation('reveal', 'open');
});

// New alternative

$('.add-alternative').click(function(){
    table_title_modal.find('input#id_title').val('');
    table_title_modal.find('textarea#id_description').val('');
    table_title_modal.find('input#id_mode').val('alternative');
    table_title_modal.find('input#id_object').val('new');
    table_title_modal.foundation('reveal', 'open');
});

// Table title modal submit

$('#table-title-modal form').submit(function(e){
    e.preventDefault();
    var form = $(this);

    // New criteria

    if ('new' == form.find('input[name="object"]').val()
        && 'criteria' == form.find('input[name="mode"]').val()) {
        $.ajax({
            url: '/ajax/',
            type: 'POST',
            data: form.serialize(),
            complete: function(xhr, data) {
                criteria = $.parseJSON(xhr.responseText);
                if (isNaN(criteria.id))
                    return;
                if (table.find('thead th').length <= 0)
                    table.find('thead tr').append('<th></th>');
                new_criteria = '<th class="criteria" id="criteria-' + criteria.id + '" data-criteria="' + criteria.id + '">'
                    + criteria.title
                    + '&nbsp;<a class="foundicon-edit edit-table-title" data-reveal-id="edit-title-modal"></a>'
                    + '&nbsp;<a class="foundicon-remove" data-reveal-id="remove-title-modal"></a>'
                    + '</th>';
                table.find('thead tr').append(new_criteria);
                table.find('tbody tr.alternative').append('<td><a class="button expand secondary select-idea">' + gettext('Select idea') + '</a></td>');
                adjust_table_overflow();
                table_title_modal.foundation('reveal', 'close');
                table.find('#criteria-' + criteria.id).highlight();
            }
        });

    // New alternative

    } else if ('new' == form.find('input[name="object"]').val()
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
                    + alternative.title
                    + '&nbsp;<a class="foundicon-edit edit-table-title" data-reveal-id="edit-title-modal"></a>'
                    + '&nbsp;<a class="foundicon-remove" data-reveal-id="remove-title-modal"></a>'
                    + '</td>';
                n_criteria = table.find('th.criteria').length;
                for (i = 0; i < n_criteria; i++) {
                    new_alternative += '<td><a class="button expand secondary select-idea">' + gettext('Select idea') + '</a></td>';
                }
                new_alternative += '</tr>';
                table.find('tbody').append(new_alternative);
                adjust_table_overflow();
                table_title_modal.foundation('reveal', 'close');
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
            console.log(item.id);
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
