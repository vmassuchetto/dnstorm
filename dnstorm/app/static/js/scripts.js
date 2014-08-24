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

$(document).on('click', '.close-reveal-modal-button', function(){
    $(this).parents('.reveal-modal').foundation('reveal', 'close');
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

$(document).on('click', '.show-problem-table', function(){
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

// Criteria on problem form

var criteria_form = $('#criteria-form.reveal-modal');
$('#criteria-form input[type="submit"]').click(function(e){
    e.preventDefault();
    var form = $('#criteria-form');
    var form_data = $('#criteria-form form').serialize() + '&new_criteria=1';
    var obj = $(this);
    obj.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: form_data,
        complete: function(xhr, data) {
            obj.removeClass('loading');
            if (data == 'success') {
                response = JSON.parse(xhr.responseText);
                // Form errors handling
                form.find('.holder').removeClass('error');
                form.find('small.error').remove();
                if (response.errors) {
                    for (e in response.errors) {
                        $('#div_id_' + e).addClass('error');
                        $('#id_' + e).after('<small class="error">' + response.errors[e] + '</small>');
                    }
                    return false;
                }
                // Created successfully
                $('#id_criteria').trigger('didAddPopup', [response.id, response.lookup_display]); // send event to django-ajax-selects
                criteria_form.find('input[type="text"],textarea').each(function(){ $(this).val(''); });
                criteria_form.foundation('reveal', 'close');
            }
        }
    });
});

// When accessing the URL directly to an idea or comment in ProblemView

if (window.location.hash.match(/#(idea|comment)-[0-9]+/)) {
    var target = $(window.location.hash);
    target.highlight('green', 2000);
}

// Vote criteria

$('.criteria-vote .stars i').on('mouseover', function(){
    p = $(this);
    while (p.length > 0) {
        $(p).addClass('selecting');
        p = p.prev('i');
    }
});

$('.criteria-vote .stars i').on('mouseout', function(){
    $(this).removeClass('selecting');
    $(this).siblings('i').removeClass('selecting');
});

$('.criteria-vote .stars i').on('click', function(){
    p = $(this);
    p.siblings('i').removeClass('selected');
    while (p.length > 0) {
        $(p).addClass('selected');
        p = p.prev('i');
    }
    $(this).parents('form').find('#id_criteria_' + $(this).data('criteria')).val($(this).index() + 1);
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
    var obj = $(this);
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

/**
 * Strategy table
 */

var table = $('.problem-table');

function adjust_table_overflow() {
    if ($('.problem-table-wrap').lenght <= 0 || !table)
        return;
    h = table.height() + 30;
    $('.problem-table-wrap').height(h);
    if (table.width() > $('.problem-table-wrap').width()) {
        $('.problem-table-wrap').jScrollPane();
    }
}

$(document).on('click', '.table-help-show', function(){
    $('.table-help').slideDown(300);
});

/**
 * Strategy table: New alternative
 */
$(document).on('click', '.new-alternative', function(){
    var button = $(this);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'new_alternative': 1,
            'problem': table.data('problem')
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                table.find('tbody').append(response.html);
                table.find('#alternative-' + response.id).highlight('green');
            }
            button.removeClass('loading');
        }
    });
    adjust_table_overflow();
});

/**
 * Strategy table: Delete alternative
 */
var alternative_delete_modal = $('#alternative-delete-modal');
$(document).on('click', '.delete-alternative', function(){
    alternative_delete_modal.data('alternative', $(this).data('alternative'));
    alternative_delete_modal.foundation('reveal', 'open');
});
$(document).on('click', '.delete-alternative-confirm', function(){
    var button = $(this);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'delete_alternative': alternative_delete_modal.data('alternative')
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                alternative_delete_modal.foundation('reveal', 'close');
                $('#alternative-' + alternative_delete_modal.data('alternative')).highlight('red').delay(200).remove();
                i = 0;
                table.find('.alternative-order').each(function(){
                    i++;
                    $(this).html(i);
                });
                adjust_table_overflow();
            }
            button.removeClass('loading');
        }
    });
});

/**
 * Strategy table: Vote
 */
$(document).on('mouseenter', '.alternative-vote .cell-wrap', function(){
    $(this).parent().addClass('hover');
});
$(document).on('mouseleave', '.alternative-vote .cell-wrap', function(){
    $(this).parent().removeClass('hover');
});
$(document).on('click', '.alternative-vote .cell-wrap', function(){

    var obj = $(this).parent();
    if (obj.hasClass('voted'))
        obj.removeClass('voted');
    else
        obj.addClass('voted');

    var vote_count = $(this);
    var alternative = $(this).closest('.alternative').data('alternative');

    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: { 'vote_alternative': alternative },
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                if (response.voted)
                    obj.addClass('voted');
                else
                    obj.removeClass('voted');
                obj.find('.vote-count').text(response.votes);
            }
        }
    });

});

/**
 * Strategy table: Select ideas
 */
$(document).on('mouseenter', '.problem-table .cell-wrap', function(){
    $(this).find('.alternative-ideas a.button').fadeIn(200);
});
$(document).on('mouseleave', '.problem-table .cell-wrap', function(){
    $(this).find('.alternative-ideas a.button').stop().fadeOut(200);
});
$(document).on('click', '.select-ideas', function(){

    var m = $('#select-idea-modal');
    m.data('alternative', $(this).data('alternative'));
    m.data('idea', {});

    // Update idea markings

    m.find('i.idea-status').each(function(){
        $(this).removeClass('checked');
    });
    $(this).parents('tr').find('.alternative-ideas span').each(function(){
        var i = $(this).data('idea');
        m.find('#idea-' + i + '-modal-item i.idea-status').addClass('checked');
        m.data('idea')[i] = i;
    });

    m.foundation('reveal', 'open');
});
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
$(document).on('click', '.problem-idea-modal-save', function(){
    var button = $(this);
    button.addClass('loading');
    var m = $('#select-idea-modal');
    var alternative_id = m.data('alternative');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: {
            'idea_alternative': 1,
            'alternative': alternative_id,
            'idea': m.data('idea')
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                $('#alternative-' + alternative_id).replaceWith(response.html);
                m.foundation('reveal', 'close');
                adjust_table_overflow();
            }
            button.removeClass('loading');
        }
    });
});

})(jQuery);
