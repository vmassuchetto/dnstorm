jQuery.noConflict();
(function($){

/* General {{{ */

if (!String.prototype.format) {
    String.prototype.format = function() {
        /**:Global:String.prototype.format

        Returns the prototype format.
        */
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined' ? args[number] : match;
        });
    };
}

function get_cookie(name) {
    /**:Global:get_cookie

    Gets a cookie from the browser.
    */
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
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
var csrftoken = get_cookie('csrftoken');

function csrf_safe_method(method) {
    /**:Global:csrf_safe_method

    Tests for HTTP methods that do not require CSRF protection.
    */
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function same_origin(url) {
    /**:Global:same_origin

    Test that a given url is a same-origin URL. Url could be relative or scheme
    relative or absolute. Allow absolute or scheme relative URLs to same
    origin, or any other URL that isn't scheme relative or absolute i.e
    relative.
    */
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    /**:Global:ajaxSetup

    Setups common ajax actions across all site.
    */
    beforeSend: function(xhr, settings) {
        /**:Global:ajaxSetup.beforeSend

        Send the token to same-origin, relative URLs only. Send the token only
        if the method warrants CSRF protection Using the CSRFToken value
        acquired earlier
        */
        if (!csrf_safe_method(settings.type) && same_origin(settings.url)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    },
    error : function(jqXHR, textStatus, errorThrown) {
        /**:Global:ajaxSetup.error

        Shows a nice error modal when and ajax error occurs.
        */
        $('#response-error-modal').foundation('reveal', 'open');
    }
});

$.fn.clearForm = function() {
    /**:Global:fn.clearForm

    Clears a form.
    */
    return this.each(function() {
        var type = this.type, tag = this.tagName.toLowerCase();
        if (tag == 'form')
            return $(':input',this).clearForm();
        if (type == 'hidden' || type == 'text' || type == 'password' || tag == 'textarea')
            this.value = '';
        else if (type == 'checkbox' || type == 'radio')
            this.checked = false;
        else if (tag == 'select')
            this.selectedIndex = -1;
    });
};

function scrollTo(selector) {
    /**:Global:scrollTo

    Scrolls the screen to the given selector.
    */
    $('html, body').animate({ scrollTop: $(selector).offset().top }, 1000);
}

$.fn.highlight = function (color, duration) {
    /**:Global:fn.highlight

    Renders a highlight animation in an object.
    */
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

/* }}} */

/* Modals {{{ */

$('.message-bar').on('click', '.close', function(){
    /**:Modals:click:.message-bar

    Hides the top message bar.
    */
    $(this).parent().parent().parent().slideUp();
});

$(document).on('click', '.close-reveal-modal-button', function(){
    /**:Modals:click:.close-reveal-modal-button

     Closes the modal cancel button. Used when we want to use a "Cancel" button
     instead of the "X" at the top.
     */
    $(this).parents('.reveal-modal').foundation('reveal', 'close');
});

/* }}} */

/* TopBar {{{ */

function activity_reset_counter() {
    /**:TopBar:activity_reset_counter

    Resets the activity counter.
    */
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

$(document).on('click', '.drafts-icon', function(e){
    /**:TopBar:click:.drafts-icon

    Show and hide the drafts box.
    */
    drafts = $('#drafts');
    drafts_box = $('#drafts-box');
    $('.scroll-box').not('#drafts').slideUp(200);
    if (drafts.is(':visible')) {
        $(this).removeClass('highlighted');
        drafts.slideUp(200);
    } else {
        drafts.slideDown(200);
        drafts_box.delay(200).jScrollPane();
    }
});

$(document).on('click', '.notification-icon', function(e){
    /**:TopBar:click:.notification-icon

    Show and hide the activity box.
    */
    activity_reset_counter();
    activity = $('#activity');
    activity_button = $('#activity .button');
    activity_box = $('#activity-box');
    $('.scroll-box').not('#activity').slideUp(200);
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

/* }}} */

// ProblemView {{{

$('.problem-tabs').on('click', '>div', function(e){
    /**:ProblemView:click:.problem-tabs

    Tab selection on the problem frontend.
    */
    e.preventDefault();
    $('.problem-tabs > div').removeClass('marked');
    $(this).addClass('marked');
    $('.problem-tab').stop().slideUp();
    $('.problem-' + $(this).data('tab')).stop().slideDown();
    window.location.hash = $(this).data('tab');
});

// }}}

// ProblemForm {{

$('.problem-form').on('click', '#id_public', criteria_form);
function criteria_form() {
    /**:ProblemForm:click:#id_public

    Show or hide the contributors section.
    */
    if ($('#id_public').is(':checked')) {
        $('.contributors-section').slideUp();
    } else {
        $('.contributors-section').slideDown();
    }
}
criteria_form();

/*$('.delete-button').on('click', function(e) {
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
}); */

$('.problem-form').on('click', '.criteria-add', function(e){
    /**:ProblemForm:Criteria:click:.criteria-add

    Copy the ``#criteria-form`` to the Problem form area. Attach triggers on
    the end as it's a recently created object.
    */
    e.preventDefault();
    $('.criteria').append($('#criteria-form').html());
    var c = $('.criteria .criteria-new:last');
    c.find('.frontend').slideUp();
    c.find('.backend').slideDown();
});

$('.problem-edit #delete-modal form').on('submit', function(e){
    /**:ProblemForm:click:.problem-edit #delete-modal

    Triggers the delete modal for criteria.
    */
    if ($(this).find('#id_delete_problem').val()) {
        return;
    }
    e.preventDefault();
    var d = $('#delete-modal');
    var f = d.find('form');
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var button = $(this);
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: f.serialize(),
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                if (response.deleted) {
                    d.foundation('reveal', 'close');
                    $('.criteria-' + response.deleted).remove();
                }
            }
        }
    });
});

$('.problem-form').on('click', '.criteria-delete', function criteria_delete(e) {
    /**:ProblemForm:click:.criteria-delete

    Toggles the delete modal for criteria.
    */
    toggle_delete('criteria', $(e.currentTarget).closest('.criteria-row').data('id'));
});

$('.problem-form').on('click', '.criteria-cancel', function(e) {
    /**:ProblemForm:click:.criteria-cancel

    Hides the criteria form and removes it if new.
    */
    row = $(this).closest('.criteria-row');
    if (row.hasClass('criteria-new')) {
        row.remove();
    } else {
        row.find('.backend').slideUp();
        row.find('.frontend').slideDown();
    }
});

$('.problem-form').on('change', 'select[name="fmt"]', function(e){
    /**:ProblemForm:change:select[name="fmt"]

    Show format-dependent fields on the form.
    */
    if ($(this).val() == 'scale') {
        $(this).closest('.backend').find('.minmax').slideDown();
    } else {
        $(this).closest('.backend').find('.minmax').slideUp();
        $(this).closest('.backend').find('.minmax input').each(function(){
            $(this).val('');
        });
    }
});

$('.problem-form').on('click', '.criteria-submit', function(e) {
    /**:ProblemForm:criteria_submit

    Submits the criteria form.
    */
    e.preventDefault();
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var row = $(this).closest('.criteria-row');
    var data = row.find('input,textarea,select').serialize() + '&problem_id=' + problem_id + '&criteria_submit=1';
    var button = $(this);
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: data,
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = JSON.parse(xhr.responseText);
                // Form errors handling
                row.find('.holder').removeClass('error');
                row.find('small.error').remove();
                if (response.errors) {
                    for (e in response.errors) {
                        row.find('#div_id_' + e).addClass('error');
                        row.find('#div_id_' + e).after('<small class="error">' + response.errors[e] + '</small>');
                    }
                    return false;
                }
                // Created successfully
                row.replaceWith(response.result);
                row.find('.backend').slideUp();
                row.find('.frontend').slideDown();
            }
        }
    });
});

$('.problem-form,.idea-edit').on('click', '.criteria-edit', function(e) {
    /**:ProblemForm:click:.criteria_edit

    Toggle a criteria form among the problem criteria.
    */
    // Hide all other rows
    $('.criteria .frontend').not(':visible').slideDown();
    $('.criteria .backend').filter(':visible').slideUp();
    // Show the activated one
    var f = $(e.currentTarget).closest('.frontend');
    f.slideUp();
    f.next().slideDown();
});

$('.problem-form,.idea-edit').on('click', '.criteria-unedit', function(e) {
    /**:ProblemForm:click:.problem-form.criteria_unedit

    Toggle a criteria form among the problem criteria.
    */
    $(this).closest('.frontend').slideDown();
    $(this).closest('.backend').slideUp();
});


var user_searching = false;
$('input#id_user_search').on('keyup', function(){
    if ($(this).val().length < 3 || user_searching) {
        return;
    }
    var button = $('#button-id-add_user');
    user_searching = true;
    var field = $(this);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: 'user_search=' + $(this).val(),
        complete: function(xhr, data) {
            field.removeClass('loading');
            if (data == 'success') {
                response = JSON.parse(xhr.responseText);
                $('.user-search-result').html(response.result);
                user_searching = false;
                button.removeClass('loading');
            }
        }
    });
});


$('.problem-form').on('click', '.user-search-selected,.user-search-result a.username', function(e){
    e.preventDefault();
});

$('.problem-form').on('click', '.user-search-selected .contributor-delete', function(e){
    e.preventDefault();
    var user_box = $(this).find('.user-box');
    if (user_box.data('username')) {
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: {
                'contributor_delete': user_box.data('username'),
                'problem': problem_id
            },
            complete: function(xhr, data) {
                if (data == 'success') {
                    response = JSON.parse(xhr.responseText);
                    $('.user-search-selected').replaceWith(response.result);
                }
            }
        });
    }
});

$('.problem-form').on('click', '.user-search-result .user-box', function(){
    if ($(this).data('username')) {
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: {
                'contributor_add': $(this).data('username'),
                'problem': problem_id
            },
            complete: function(xhr, data) {
                if (data == 'success') {
                    response = JSON.parse(xhr.responseText);
                    $('.user-search-selected').replaceWith(response.result);
                }
            }
        });
    } else if ($(this).data('email')) {
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: 'invitation_add=' + $(this).data('email') + '&problem=' + problem_id,
            complete: function(xhr, data) {
                if (data == 'success') {
                    response = JSON.parse(xhr.responseText);
                    $('.user-search-selected').html(response.result);
                }
            }
        });
    }
});

/* }}} */

$('.problem-tabs').ready(function(){
    /**:Problem:problem-tabs

    Actions related to hyperlinks for problem view
    */

    // When accessing the URL directly to a tab

    if (window.location.hash.match(/^#(criteria|ideas|alternatives)$/)) {
        $('.problem-tabs').find('[data-tab="' + window.location.hash.replace('#', '') + '"]').trigger('click');
    } else if (window.location.hash.match(/^#(idea|comment|criteria|alternative)-[0-9]+$/)) {
        $('.problem-tabs').find('[data-tab="ideas"]').addClass('marked');
        var target = $(window.location.hash);
        target.highlight('green', 2000);
    } else {
        $('.problem-tabs').find('[data-tab="description"]').addClass('marked');
    }

    $('.problem-tabs > div').height($('.problem-tabs').height());
    r = /.*#idea-([0-9]+).*/;
    idea_id = parseInt(document.URL.replace(r, "$1", "$0"));
    if (idea_id) {
        $('.problem-tab').stop().slideUp();
        $('.problem-ideas').stop().slideDown();
        $('.problem-tab-selector').find('[data-tab="ideas"]').addClass('marked');
        $(this).addClass('marked');
        setTimeout(function(){
            scrollTo('#idea-' + idea_id);
        }, 3000);
    }
});

/**
 * Problem form: resend pending invitations
 */

$(document).on('click', '.resend-button', function(e) {
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

// Vote criteria

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

/**
 * Idea: Likes
 */

$(document).on('mouseenter', '.like-bulb', function(){
    $(this).addClass('highlighted');
});
$(document).on('mouseleave', '.like-bulb', function(){
    $(this).removeClass('highlighted');
});
$(document).on('click', '.idea-like', function(){
    var vote = $(this);
    var counter = $(this).find('.idea-like-counter');
    if (vote.hasClass('voted'))
        counter.text(parseInt(counter.text()) - 1);
    else
        counter.text(parseInt(counter.text()) + 1);
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: 'idea_like=' + $(this).data('idea'),
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                if (response.voted)
                    vote.addClass('voted');
                else
                    vote.removeClass('voted');
                counter.text(response.counter);
            }
        }
    });
});

$(document).on('click', '.alternative-like', function(){
    var vote = $(this);
    var counter = $(this).find('.alternative-like-counter');
    if (vote.hasClass('voted'))
        counter.text(parseInt(counter.text()) - 1);
    else
        counter.text(parseInt(counter.text()) + 1);
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: 'alternative_like=' + $(this).data('alternative'),
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                if (response.voted)
                    vote.addClass('voted');
                else
                    vote.removeClass('voted');
                counter.text(response.counter);
            }
        }
    });
});

$('.problem').on('click', '.comment-button', function(e){
    /**:Comment:click:.action-comment

    Show the comment form in the proper place for ideas and criteria.
    */
    e.preventDefault();
    var form = $('#comment-form');
    var new_form = form.clone();
    var obj;
    if ($(this).data('problem')) {
        id = $(this).data('problem');
        new_form.find('input#id_problem').val(id);
        obj = $('div#comment-form-problem-' + id);
    } else if ($(this).data('idea')) {
        id = $(this).data('idea');
        new_form.find('input#id_idea').val(id);
        obj = $('div#comment-form-idea-' + id);
    } else if ($(this).data('criteria')) {
        id = $(this).data('criteria');
        new_form.find('input#id_criteria').val(id);
        obj = $('div#comment-form-criteria-' + id);
    } else if ($(this).data('alternative')) {
        id = $(this).data('alternative');
        new_form.find('input#id_alternative').val(id);
        obj = $('div#comment-form-alternative-' + id);
    }
    obj.html(new_form.html()).removeClass('hide');
});

// Comment form submit

$('.problem').on('submit', '.comment-form form', function(e){
    /**:Comment:submit:.comment-form>form

    Submits a comment.
    */
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
        data: 'comment_new=1&' + $(this).serialize(),
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                target = $(response.target);
                target.append(response.html);
                target.find('.comment').last().highlight();
                form_wrap.find('textarea').val('');
            }
        }
    });
});

$(document).on('click', 'a.display-more', function(e){
    $(this).parents('.comment').slideUp(300);
    $(this).parents('.comments').find('.hidden').slideDown(300);
    $(this).remove();
});

/**
 * Format DeleteForm for delete actions
 */

function toggle_delete(type, id) {
    var delete_modal = $('#delete-modal');
    delete_modal.find('#id_delete_problem,#id_delete_idea,#id_delete_comment,#id_delete_criteria').each(function(){
        $(this).val('');
    });
    if (type == 'problem') {
        delete_modal.find('#id_delete_problem').val(id);
    } else if (type == 'idea') {
        delete_modal.find('#id_delete_idea').val(id);
    } else if (type == 'comment') {
        delete_modal.find('#id_delete_comment').val(id);
    } else if (type == 'criteria') {
        delete_modal.find('#id_delete_criteria').val(id);
    }
    delete_modal.foundation('reveal', 'open');
}

$(document).on('click', '.problem-delete', function(){
    toggle_delete('problem', $(this).data('problem'));
});
$(document).on('click', '.idea-delete', function(){
    toggle_delete('idea', $(this).data('idea'));
});
$(document).on('click', '.comment-delete', function(){
    toggle_delete('comment', $(this).data('comment'));
});

$(document).on('click', '.new-alternative', function(){
    /**:ProblemView:click:.new-alternative

    Add new alternative to problem.
    */
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
            'problem': problem_id
        },
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            $('.problem-alternatives .panel').remove();
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                $('.problem-alternatives .new-alternative').parent().before(response.html);
                $('.problem-alternatives').height('auto');
            }
        }
    });
});

var alternative_delete_modal = $('#alternative-delete-modal');
$(document).on('click', '.delete-alternative', function(){
    /**:ProblemView:click:.delete-alternative

    Pops the confirmation dialog to delete an alternative.
    */
    alternative_delete_modal.data('alternative', $(this).data('alternative'));
    alternative_delete_modal.foundation('reveal', 'open');
});
$(document).on('click', '.delete-alternative-confirm', function(){
    /**:ProblemView:click:.delete-alternative-confirm

    Confirms the deletion of an alternative and sends the ajax action for it.
    */
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
                response = $.parseJSON(xhr.responseText);
                alternative_delete_modal.foundation('reveal', 'close');
                $('.alternative-' + response.deleted).remove();
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

$(document).on('click', '.select-ideas', function(){
    /**:ProblemView:.select-ideas

    Shows the ideas modal to select them for alternatives.
    */
    var m = $('#select-idea-modal');
    m.data('alternative', $(this).data('alternative'));
    m.data('idea', {});

    // Update idea markings

    m.find('i.idea-status').each(function(){
        $(this).removeClass('checked');
    });
    $(this).parents('.alternative-row').find('.alternative-ideas a').each(function(){
        var i = $(this).data('idea');
        m.find('#idea-' + i + '-modal-item i.idea-status').addClass('checked');
        m.data('idea')[i] = i;
    });

    m.foundation('reveal', 'open');
});
$(document).on('click', '.problem-idea-modal', function(){
    /**:ProblemView:.problem-idea-modal

    Select ideas in a modal.
    */
    var m = $('#select-idea-modal');
    var i = $(this).find('.idea-row').data('id');
    var s = $(this).find('i.idea-status');
    if (m.data('idea') === undefined)
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
    /**:ProblemView:.problem-idea-modal-save

    Saves the selected ideas in a modal.
    */
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
                $('.alternative-' + alternative_id).replaceWith(response.html);
                m.foundation('reveal', 'close');
            }
        }
    });
});

// Foundation

$(document).foundation();

})(jQuery);
