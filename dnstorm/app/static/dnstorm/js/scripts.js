jQuery.noConflict();
(function($){

// String formatting

if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

// Get unique IDs

function get_id() {
    id = Math.floor((Math.random()*10000)+1); 
    while ($('#' + id).length > 0)
        id = Math.floor((Math.random()*10000)+1);
    return id;
}

// CSRF

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

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Foundation

$(document).foundation();
$(document).foundation('joyride', 'start');

// Highlight

$.fn.highlight = function (color, duration) {
    if (!duration)
        duration = 1000;
    if (color == 'red')
        color = '#FF6666';
    else
        color = '#CCCCCC';
    var e = $(this[0]);
    var original = e.css('backgroundColor');
    return e.animate({ backgroundColor: color }, duration, null, function(){
        e.animate({ backgroundColor:original });
    });
};

// Modal cancel button
// When we want to use a "Cancel" button instead of the "X" at the top

$('.close-reveal-modal-button').click(function(){
    $(this).parents('.reveal-modal').foundation('reveal', 'close');
});

// Criteria tag button renderers

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

// Problem criterias autocomplete in ProblemCreateView and ProblemUpdateView

$('.problem-criteria-select .text').autocomplete({
    minLength: 2,
    source: '/ajax/',
    messages: {
        noResults: '',
        results: function() {}
    },
    response: function(event, ui) {
        output = '';
        exact_match = false;
        if (ui.content.length > 0) {
            for (i in ui.content) {
                item = ui.content[i];
                output += criteria_field(item.id, item.label, item.description)
                if (event.target.innerHTML == item.label)
                    exact_match = true;
            }
        }

        if (!exact_match)
            output += criteria_field(0, $('.problem-criteria-select .text').text(), gettext('Click above to create this criteria.'));

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
// Datepicker

$('.dateinput').fdatepicker({'format': 'dd/mm/yyyy'});

// Add quantifiers entries

function quantifier_row(q) {
    id = get_id();
    base_str = '<div class="row quantifier-entry">'
        + '<div class="columns large-2"><a class="button secondary tiny radius" href="javascript:void(0)">{0}</a></div>'
        + '<div class="columns large-3"><input type="text" placeholder="{1}" value="{2}" name="{3}"></div>'
        + '<div class="columns large-5"><textarea placeholder="{4}" name="{5}">{6}</textarea></div>'
        + '<div class="columns large-2">'
            + '<a class="button alert tiny radius quantifier-remove-dialog" href="javascript:void(0)">'
                + '<i class="foundicon-minus"></i>&nbsp;{7}'
            + '</a>'
        + '</div>'
        + '</div>'
    return base_str.format(
        q.format,
        gettext('Quantifier name'),
        '',
        'quantifiername_new' + id + '_' + q.format,
        gettext('Help text'),
        'quantifierhelp_new' + id + '_' + q.format,
        '',
        gettext('Remove'))
}

$('#quantifier-add').click(function(){
    var q = $('#id_quantifier_format option:selected');
    if ('' == q)
        return false;
    html = quantifier_row({'format': q.val(), 'label': q.text()});
    $('#quantifiers').append(html);
});

// Remove quantifier entries

$(document).on('click', '.quantifier-remove-dialog', function(e){
    $('#quantifier-remove-modal').data('to-remove', $(this).parents('.quantifier-entry'));
    $('#quantifier-remove-modal').foundation('reveal', 'open');
    e.preventDefault();
});

$(document).on('click', '.quantifier-remove', function(e){
    $('#quantifier-remove-modal').data('to-remove').remove();
    $('#quantifier-remove-modal').foundation('reveal', 'close');
    e.preventDefault();
});

// Criteria modal form in ProblemCreateView and ProblemUpdateView

$('#criteria-modal form').submit(function(e){
    e.preventDefault();
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        dataType: 'json',
        data: $(this).serialize(),
        success: function(data) {
            modal = $('#criteria-modal');
            if (data.errors) {
                for (e in data.errors) {
                    elem = modal.find('#div_id_' + e);
                    if (!elem.hasClass('error'))
                        elem.addClass('error').append('<small class="error">' + data.errors[e] + '</small>')
                }
            } else {
                // Clear and hide form for future use
                modal.foundation('reveal', 'close');
                modal.find('#id_name').val('');
                modal.find('#criteria_description').val('');
                // Update 'parent' select field
                modal.find('#id_parent').append('<option value="' + data.id + '">' + data.name + '</option>');
                // Insert button
                button = $('.problem-criteria-result li a[data-id="0"]');
                button.data('id', data.id);
                button.attr('data-id', data.id);
                button.siblings('.description').text(data.description);
                criteria_add_button(button);
            }
        }
    });
});

// Remove criteria and input data in ProblemCreateView and ProblemUpdateView

$('.problem-criteria-select').on('click', 'a.button', function(){
    id = $(this).remove().data('id');
    $('.problem-form input').filter(function() { return this.name.match(/^criteria_[0-9]+$/); }).filter('[value="' + id + '"]').remove();
    $('.tooltip').fadeOut();
});

// Focus writable area to simulate an input box in ProblemCreateView and ProblemUpdateView

$('.problem-criteria-select').click(function(){
    $(this).find('.text').focus();
});

// Show advanced options in ProblemCreateView and ProblemUpdateView

$('.problem-edit fieldset:gt(0)').hide();
$('#advanced').click(function(){
    $('.problem-edit fieldset:gt(0)').each(function(){ $(this).fadeIn(300); });
    $(this).remove();
});

// Revision rendering in ProblemRevisionView

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

$(document).on('click', '.problem-comment', function(){
    $('.problem-comment-form').fadeIn();
});

$(document).on('click', '.idea-comment', function(){
    $('div#idea-' + parseInt($(this).data('idea')) + '-comment-form.comment-form').fadeIn();
});

$('.show-problem-table').click(function(){
    if ($('#problem-table-row').css('display') == 'none') {
        $('#problem-table-row').fadeIn(300);
        adjust_table_overflow();
    } else {
        $('#problem-table-row').fadeOut(300);
    }
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

$('.problem-idea-form-button').click(function(){
    $('.problem-idea-button').fadeOut(300);
    CKEDITOR.instances.id_content.resize('100', '340');
    $('.problem-idea-form').delay(300).fadeIn(300);
});

// When accessing the URL directly to an idea or comment in ProblemView

if (window.location.hash.match(/#(idea|comment)-[0-9]+/)) {
    var target = $(window.location.hash);
    target.highlight('green', 2000);
}

// Delete idea

$(document).on('click', '.problem-idea-delete-toggle', function(){
    var idea = $(this).parents('.problem-idea');
    var idea_id = $(this).data('idea');
    var obj = $(this);
    obj.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'delete_idea': idea_id
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                if (xhr.responseText == 'undelete')
                    idea.addClass('deleted');
                else
                    idea.removeClass('deleted');
                idea.find('.problem-idea-delete-toggle').text(xhr.responseText);
            }
            obj.removeClass('loading');
        }
    });
});

// Comment form submit

$('.comment-form form').submit(function(e){
    e.preventDefault();
    var problem = $(this).parent().data('problem');
    var idea = $(this).parent().data('idea');
    var comments;
    if (problem)
        comments = $('#comments-problem-' + problem);
    else if (idea)
        comments = $('#comments-idea-' + idea);
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

// Delete comment

$(document).on('click', '.comment-delete-toggle', function(){
    var obj = $(this)
    obj.addClass('loading');
    var comment = $(this).parents('.comment');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'delete_comment': $(this).data('comment')
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                c = comment.find('.comment-delete-toggle');
                if (xhr.responseText == 'undelete') {
                    comment.addClass('deleted');
                    c.removeClass('comment-delete');
                    c.addClass('comment-undelete');
                } else {
                    c.removeClass('comment-undelete');
                    c.addClass('comment-delete');
                    comment.removeClass('deleted');
                }
            }
            obj.removeClass('loading');
        }
    });
});

// Idea voting

$('.problem-idea .voting a').click(function() {

    if (typeof $(this).attr('disabled') !== 'undefined'
        || typeof $(this).data('reveal-id') !== 'undefined')
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
            count = parseInt(xhr.responseText);
            // Reset stuff if things go wrong
            if (isNaN(count)) {
                upvote.removeClass('success');
                downvote.removeClass('alert');
                counter.html(parseInt(counter.html()) - weight);
            } else {
                counter.html(count);
            }
        }
    });

});

// Alterantive voting

$(document).on('click', '.alternative .voting a', function() {

    if (typeof $(this).attr('disabled') !== 'undefined'
        || typeof $(this).data('reveal-id') !== 'undefined')
        return;

    var sum;
    var vote = $(this).parents('td');
    var voted = vote.hasClass('voted');
    var alternative = $(this).data('alternative');

    if (voted) {
        vote.removeClass('voted');
        sum = -1;
    } else {
        vote.addClass('voted');
        sum = 1;
    }

    var counter = $(this).siblings('.vote-count');
    counter.html(parseInt(counter.text()) + sum);

    $.ajax({
        url: '/ajax/',
        data: {
            'alternative': $(this).data('alternative'),
            'weight': sum
        },
        complete: function(xhr, data) {
            count = parseInt(xhr.responseText);
            // Reset stuff if things go wrong
            if (isNaN(count)) {
                if (voted)
                    vote.addClass('voted');
                else
                    vote.removeClass('voted');
                counter.html(parseInt(counter.html()) - sum);
            } else {
                counter.html(count);
            }
        }
    });

});


// TableView section

var table = $('.problem-table');
var alternative_add_modal = $('#alternative-add-modal');
var alternative_remove_modal = $('#alternative-remove-modal');
var problem_remove_modal = $('#alternative-remove-modal');

// Table overflow adjust in TableView

function adjust_table_overflow() {
    if ($('.problem-table-wrap').lenght <= 0 || !table)
        return;
    h = table.height() + 30;
    $('.problem-table-wrap').height(h);
    if (table.width() > $('.problem-table-wrap').width()) {
        $('.problem-table-wrap').jScrollPane();
    }
}

$(document).on('mouseenter', '.problem-table .cell-wrap', function(){
    $(this).find('a.button').fadeIn(200);
});
$(document).on('mouseleave', '.problem-table .cell-wrap', function(){
    $(this).find('a.button').stop().fadeOut(200);
});

// New alternative in TableView

$(document).on('click', '.add-alternative', function(){
    alternative_add_modal.find('input#id_title').val('');
    alternative_add_modal.find('textarea#id_description').val('');
    alternative_add_modal.find('input#id_mode').val('alternative');
    alternative_add_modal.find('input#id_object').val('new');
    alternative_add_modal.foundation('reveal', 'open');
});

// Remove alternative in TableView

$(document).on('click', '.remove-alternative', function(){
    alternative_remove_modal.data('alternative', $(this).data('alternative'));
    alternative_remove_modal.foundation('reveal', 'open');
});

$(document).on('click', '.remove-alternative-confirm', function(){
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: {
            'mode': 'remove-alternative',
            'object': alternative_remove_modal.data('alternative')
        },
        complete: function(xhr, data) {
            alternative_remove_modal.foundation('reveal', 'close');
            $('#alternative-' + alternative_remove_modal.data('alternative')).highlight('red').delay(1000).fadeOut(500).delay(500).remove();
            adjust_table_overflow();
        }
    });
});

// Submit new alternative in TableView

$(document).on('submit', '#alternative-add-modal form', function(e){
    e.preventDefault();
    var form = $(this);
    if ('new' == form.find('input[name="object"]').val()
        && 'alternative' == form.find('input[name="mode"]').val()) {
        $.ajax({
            url: '/ajax/',
            type: 'POST',
            data: form.serialize(),
            complete: function(xhr, data) {
                if (xhr.responseText)
                    alternative = $.parseJSON(xhr.responseText);
                else
                    return;
                if (isNaN(alternative.id))
                    return;

                // Alternative row

                new_alternative = '<tr class="alternative" id="alternative-' + alternative.id + '" data-alternative="' + alternative.id + '">'
                    + '<td class="vertical-title">'
                        + '<div class="title-inner title-admin-with-button" title="' + alternative.description + ' data-tooltip">'
                        + '&nbsp;<a class="foundicon-remove remove-alternative button alert radius tiny" data-alternative="' + alternative.id + '"></a>'
                        + alternative.name
                        + '</div>'
                    + '</td>'
                    + '<td class="voting">'
                        + '<a href="javascript:void(0);" class="vote" data-alternative="' + alternative.id + '"><i class="foundicon-idea"></i></a>'
                        + '<span class="vote-count">0</span>'
                    + '</td>';
                table.find('th.criteria').each(function(){
                    datas = 'data-problem="' + alternative.problem + '" data-alternative="' + alternative.id + '" data-criteria="' + $(this).data('criteria') + '"';
                    new_alternative += '<td><div class="cell-wrap"><a class="button expand radius secondary select-idea" ' + datas + '>' + gettext('Select idea') + '</a></div></td>';
                });

                // Extra column for criterias if they are being used

                if (table.hasClass('with-criterias'))
                    new_alternative += '<td></td>';

                new_alternative += '</tr>';

                table.find('tbody').append(new_alternative);
                adjust_table_overflow();
                alternative_add_modal.foundation('reveal', 'close');
                table.find('#alternative-' + alternative.id).highlight();
            }
        });
    }
});

// Select idea in the problem table

$(document).on('click', '.select-idea', function(){
    var m = $('#select-idea-modal');
    m.data('problem', $(this).data('problem'));
    m.data('criteria', $(this).data('criteria'));
    m.data('alternative', $(this).data('alternative'));
    m.data('item', $(this).parent());
    m.data('idea', {});

    // Updata idea markings

    m.find('i.idea-status').each(function(){
        $(this).removeClass('checked');
    });
    $(this).parent().find('span').each(function(){
        var i = $(this).data('idea');
        m.find('#idea-' + i + '-modal-item i.idea-status').addClass('checked');
        m.data('idea')[i] = i;
    });

    m.foundation('reveal', 'open');
});

// Select ideas in the select modal in TableView

$(document).on('click', '.problem-idea-modal', function(){
    var m = $('#select-idea-modal');
    var i = $(this).find('.problem-idea').data('idea');
    var s = $(this).find('i.idea-status');

    if (m.data('idea') == undefined)
        m.data('idea', {});

    if (s.hasClass('checked')) {
        s.removeClass('checked');
        delete m.data('idea')[i];
    } else {
        s.addClass('checked');
        m.data('idea')[i] = i;
    }
});

// Save selected ideas

$(document).on('click', '.problem-idea-modal-save', function(){
    var m = $('#select-idea-modal');
    var item = m.data('item');
    var quant = m.data('item').parents('tr').find('td:last-child');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: {
            'problem': m.data('problem'),
            'criteria': m.data('criteria'),
            'alternative': m.data('alternative'),
            'idea': m.data('idea')
        },
        complete: function(xhr, data) {
            item.html('');
            if (xhr.responseText)
                items = $.parseJSON(xhr.responseText);
            else
                return;
            if (items.length <= 0) {
                m.foundation('reveal', 'close');
                return;
            }

            // Alternatives

            for (i in items.ideas) {
                item.append('<span class="label secondary radius" data-idea="' + items.ideas[i].id + '">' + items.ideas[i].title + '</span>');
            }
            datas = 'data-problem="' + items.ideas[i].problem + '" '
                + 'data-criteria="' + items.ideas[i].criteria + '" '
                + 'data-alternative="' + items.ideas[i].alternative + '"';
            item.append('<a class="button secondary radius expand select-idea hidden" '+ datas + '>' + gettext('Select idea') + '</a>');

            // Quantifiers

            quant.html('');
            for (q in items.quantifiers) {
                quant.append('<span class="label radius">' + items.quantifiers[q].name + '&nbsp;|&nbsp;' + items.quantifiers[q].value + '</span>');
            }

            m.foundation('reveal', 'close');
            item.highlight();
            adjust_table_overflow();
        }
    });
});

})(jQuery);
