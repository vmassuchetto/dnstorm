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

function scrollTo(selector) {
    $('html, body').animate({ scrollTop: $(selector).offset().top }, 1000);
}

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

// Show problem table on click

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

// Scroll to idea form

$('.problem-idea-form-button').click(function(){
    scrollTo('.problem-idea-form');
});

/**
 * Notifications
 */

function activity_reset_counter() {
    var notification = $('.notification');
    var activity_counter = $('.notification .counter');
    if (parseInt(activity_counter.text()) > 0) {
        activity_counter.text('0');
        notification.removeClass('alert');
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: 'activity_reset_counter=1',
        });
    }
}

$(document).on('click', '.notification-icon', function(e){
    activity_reset_counter();
    activity = $('#activity');
    activity_button = $('#activity .button');
    activity_box = $('#activity-box');
    if (activity.is(':visible')) {
        $(this).removeClass('highlighted');
        activity.slideUp(200);
    } else {
        $(this).addClass('highlighted');
        activity.slideDown(200);
        activity_box.delay(200).jScrollPane();
        activity_button.delay(200).focus();
    }
});

/**
 * Problem form: idea
 */

$(document).on('submit', '.problem-idea-form form', function(e){
    e.preventDefault();
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var button = $(this).find('input[type="submit"]');
    button.attr('disabled', true);
    button.addClass('loading');
    var form = $('.problem-idea-form form');
    form.find('textarea[name="content"]').val(CKEDITOR.instances.id_content.getData());
    var form_data = form.serialize() + '&new_idea=1';
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: form_data,
        complete: function(xhr, data) {
            if (data == 'success') {
                button.attr('disabled', false);
                button.removeClass('loading');
                response = JSON.parse(xhr.responseText);
                // Form errors handling
                form.find('.holder').removeClass('error');
                form.find('small.error').remove();
                if (response.errors) {
                    for (e in response.errors) {
                        if (e == '__all__') {
                            form.find('h5').after('<small class="error">' + response.errors[e] + '</small>');
                        } else {
                            $('#div_id_' + e).addClass('error');
                            $('#id_' + e).after('<small class="error">' + response.errors[e] + '</small>');
                        }
                    }
                    return false;
                }
                // Created successfully
                form.find('input[type="text"],textarea').val('');
                CKEDITOR.instances['id_content'].setData('');
                $('.criteria-vote .stars i').removeClass('selected');
                $(response.html).appendTo('.problem-ideas').highlight('green', 2000);
            }
        }
    });
});

/**
 * Problem form: criteria
 */

var criteria_form = $('#criteria-form.reveal-modal');

// New criteria

$('.criteria-new').on('click', function(e){
    e.preventDefault();
    criteria_form.trigger('reset');
    criteria_form.foundation('reveal', 'open');
});

// Criteria submit

function criteria_form_trigger(){
    $('#criteria-form input[type="submit"]').on('click', function(e){
        e.preventDefault();
        if ($(this).attr('disabled') == 'disabled')
            return false;
        var form = $('#criteria-form');
        var form_data = $('#criteria-form form').serialize() + '&new_criteria=1';
        var button = $(this);
        button.attr('disabled', true);
        button.addClass('loading');
        $.ajax({
            url: '/ajax/',
            type: 'POST',
            data: form_data,
            complete: function(xhr, data) {
                button.attr('disabled', false);
                button.removeClass('loading');
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
                    obj = $('#id_criteria_on_deck_' + response.id);
                    if (obj.length > 0) {
                        obj.find('.criteria-name').text(response.name);
                        obj.find('.criteria-description').text(response.description);
                    } else {
                        $('#id_criteria').trigger('didAddPopup', [response.id, response.lookup_display]); // send event to django-ajax-selects
                    }
                    criteria_form.trigger('reset');
                    criteria_form.foundation('reveal', 'close');
                }
            }
        });
    });
}
criteria_form_trigger();

// Criteria edit

$(document).ready(function(){
    $('.criteria-edit').on('click', function(e){
        $(this).data('id');
        e.preventDefault();
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: 'criteria_form=' + $(this).data('id'),
            complete: function(xhr, data) {
                if (data == 'success') {
                    response = JSON.parse(xhr.responseText);
                    criteria_form.find('form').replaceWith(response.html);
                    criteria_form.foundation('reveal', 'open');
                    criteria_form_trigger();
                }
            }
        });
    })
});


/**
 * Problem: contributor management
 */

$(document).on('submit', '#contributor-form', function(e){
    e.preventDefault();
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var form = $(this);
    var button = $(this).find('input[type="submit"]');
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: form.serialize() + '&action=contributor',
        complete: function(xhr, data) {
            button.removeClass('loading');
            button.attr('disabled', false);
            if (data == 'success') {
                $('#contributors-modal').foundation('reveal', 'close');
            }
        }
    });
});

/**
 * Problem form: resend pending invitations
 */

$('.resend-button').on('click', function(e) {
    e.preventDefault();
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var button = $(this);
    var invitation = button.data('invitation');
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: 'resend_invitation=' + invitation,
        complete: function(xhr, data) {
            button.removeClass('loading');
            if (data == 'success') {
                button.text('OK');
            }
        }
    });
});

/**
 * Problem form: delete pending invitations
 */

$('.delete-button').on('click', function(e) {
    e.preventDefault();
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var button = $(this);
    var invitation = button.data('invitation');
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: 'delete_invitation=' + invitation,
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                $('#invitation-' + invitation).fadeOut(200).delay(200).remove();
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

var timeout;
$('.criteria-button:not(.expanded)').hover(function() {
    var description = $(this).find('.criteria-description');
    if (!timeout) {
        timeout = window.setTimeout(function() {
            timeout = null;
            description.fadeIn();
        }, 500);
    }
}, function () {
    var description = $(this).find('.criteria-description');
    if (timeout) {
        window.clearTimeout(timeout);
        timeout = null;
    } else {
        description.fadeOut();
    }
});

// Show comment on click

$(document).on('click', '.action-comment', function(e){
    e.preventDefault();
    var form = $('#comment-form');
    var new_form = form.clone();
    var obj;
    if ($(this).data('problem')) {
        new_form.find('input#id_problem').val($(this).data('problem'));
        obj = $('div#comment-form-problem');
    } else if ($(this).data('idea')) {
        new_form.find('input#id_idea').val($(this).data('idea'));
        obj = $('div#comment-form-idea-' + $(this).data('idea'));
    }
    obj.html(new_form.html()).removeClass('hide');
});

// Comment form submit

$(document).on('submit', '.comment-form form', function(e){
    e.preventDefault();
    var button = $(this).find('input[type="submit"]');
    if (button.attr('disabled') == 'disabled')
        return false;
    var form_wrap = $(this).parent();
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: 'new_comment=1&' + $(this).serialize(),
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                $(response.target).append(response.html);
                $(response.target).find('.comment').last().highlight();
                form_wrap.find('textarea').val('');
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

var table_row = $('#problem-table-row');
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

$(document).on('click', '.table-button', function(){
    table_row.slideToggle(300);
});

$(document).on('click', '.table-help-show', function(){
    $(this).next().slideToggle(300);
});

/**
 * Strategy table: New alternative
 */
$(document).on('click', '.new-alternative', function(){
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var button = $(this);
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'new_alternative': 1,
            'problem': table.data('problem')
        },
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                table.find('tbody').append(response.html);
                table.find('#alternative-' + response.id).highlight('green');
            }
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
    if ($(this).attr('disabled') == 'disabled')
        return false;
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'delete_alternative': alternative_delete_modal.data('alternative')
        },
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
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
    if ($(this).attr('disabled') == 'disabled')
        return false;
    button.attr('disabled', true);
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
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                $('#alternative-' + alternative_id).replaceWith(response.html);
                m.foundation('reveal', 'close');
                adjust_table_overflow();
            }
        }
    });
});

})(jQuery);
