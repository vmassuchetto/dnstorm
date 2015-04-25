jQuery.noConflict();
(function($){

if (!String.prototype.format) {
    String.prototype.format = function() {
        /***
        Returns the prototype format.
        ***/
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined' ? args[number] : match;
        });
    };
}

function get_cookie(name) {
    /***
    Gets a cookie from the browser.
    ***/
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
    /***
    Tests for HTTP methods that do not require CSRF protection.
    ***/
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function same_origin(url) {
    /***Global:same_origin

    Test that a given url is a same-origin URL. Url could be relative or scheme
    relative or absolute. Allow absolute or scheme relative URLs to same
    origin, or any other URL that isn't scheme relative or absolute i.e
    relative.
    ***/
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    /***
    Setups common ajax actions across all site.
    ***/
    beforeSend: function(xhr, settings) {
        /***
        Send the token to same-origin, relative URLs only. Send the token only
        if the method warrants CSRF protection Using the CSRFToken value
        acquired earlier
        ***/
        if (!csrf_safe_method(settings.type) && same_origin(settings.url)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    },
    error : function(jqXHR, textStatus, errorThrown) {
        /***
        Shows a nice error modal when and ajax error occurs.
        ***/
        $('#response-error-modal').foundation('reveal', 'open');
    }
});

$.fn.clearForm = function() {
    /***
    Clears a form.
    ***/
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
    /***
    Scrolls the screen to the given selector.
    ***/
    $('html, body').animate({ scrollTop: $(selector).offset().top }, 200);
}

$.fn.highlight = function (color, duration) {
    /***
    Renders a highlight animation in an object.
    ***/
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

$(document).ready(function(){
    /***
    Sets stickable effect on elements.
    ***/
    var s = $('.stickable');
    if (s.length === 0) return false;
    s.each(function(){
        s.data('top', s.offset().top);
        s.data('left', s.offset().left);
        s.data('width', s.width());
    });
    $(window).scroll(function(){
        var windowpos = $(window).scrollTop();
        s.each(function(){
            if ($(this).hasClass('stick')) {
                if (windowpos < $(this).data('top')) {
                    $(this).css('width', 'auto');
                    $(this).removeClass('stick');
                }
                return;
            }
            if (windowpos >= $(this).data('top')){
                $(this).css('width', $(this).data('width'));
                $(this).addClass("stick");
            }
        });
    });
});

$('.message-bar').on('click', '.close', function(){
    /***
    Hides the top message bar.
    ***/
    $(this).parent().parent().parent().slideUp(200);
});

$(document).on('click', '.close-reveal-modal-button', function(){
    /***
     Closes the modal cancel button. Used when we want to use a "Cancel" button
     instead of the "X" at the top.
     ***/
    $(this).parents('.reveal-modal').foundation('reveal', 'close');
});

function activity_reset_counter() {
    /***
    Resets the activity counter.
    ***/
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
    /***
    Show and hide the drafts box.
    ***/
    drafts = $('#drafts');
    drafts_box = $('#drafts-box');
    $('.scroll-box').not('#drafts').hide();
    if (drafts.is(':visible')) {
        $(this).removeClass('highlighted');
        drafts.hide();
    } else {
        drafts.show();
        drafts_box.delay(200).jScrollPane();
    }
});

$(document).on('click', '.notification-icon', function(e){
    /***
    Show and hide the activity box.
    ***/
    activity_reset_counter();
    activity = $('#activity');
    activity_button = $('#activity .button');
    activity_box = $('#activity-box');
    $('.scroll-box').not('#activity').hide();
    if (activity.is(':visible')) {
        $(this).removeClass('highlighted');
        activity.hide();
    } else {
        $(this).addClass('highlighted');
        activity.show();
        activity_box.jScrollPane();
        activity_button.focus();
    }
});

$(document).on('click', '.login-icon', function(e){
    /***
    Show and hide the login form.
    ***/
    login = $('#login');
    $('.scroll-box').not('#login').hide();
    if (login.is(':visible')) {
        login.hide();
    } else {
        login.show();
    }
});

function toggle_help_panel() {
    /***
    Show the help panel.
    ***/
    if  ($('.help').is(':visible')) {
        $('.help').slideUp(200);
        return;
    } else if ($('.help').not(':visible') && $('.help').html().length > 1) {
        $('.help').slideDown(200);
        return;
    }
    var button = $(this);
    if (button.attr('disabled') == 'disabled')
        return false;
    button.attr('disabled', true);
    button.addClass('loading');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: 'help=1',
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                target = $('.help');
                target.html(response.html);
                target.height(400);
                target.slideDown();
                target.height('auto');
                $(document).foundation({'orbit': {
                    'next_on_click': false,
                    'navigation_arrows': false,
                    'slide_number': false,
                }});
                var data = [
                    { value: 1/5, color: "#666666", highlight: "#a1a1a1" },
                    { value: 1/5, color: "#666666", highlight: "#a1a1a1" },
                    { value: 1/5, color: "#666666", highlight: "#a1a1a1" },
                    { value: 1/5, color: "#a1a1a1", highlight: "#666666" },
                    { value: 1/5, color: "#a1a1a1", highlight: "#666666" },
                ];
                var options = {
                    'showLabels': false,
                    'showTooltips': false,
                    'showScale': false
                };
                var chart = new Chart(document.getElementById("pie").getContext("2d")).Doughnut(data, options);
            }
        }
    });
}

$(document).on('click', '.theory-help a.toggle', toggle_help_panel);

$(document).ready(function(){
    /***
    Trigger the help panel on page load.
    ***/
    if ($('body').hasClass('show-help')) {
        setTimeout(function(){
            console.log('trigger');
            toggle_help_panel();
        }, 200);
    }
});


function criteria_value() {
    /***
    Show format-dependent fields on the form.
    ***/
    var f = $('.criteria form');
    var v = f.find('select[name="fmt"]').val();
    if (v == 'scale') {
        f.find('.minmax').show();
    } else {
        f.find('.minmax').hide();
        f.find('.minmax input').each(function(){
            $(this).val('');
        });
    }
}
$('.criteria form').on('change', 'select[name="fmt"]', criteria_value);
$('.criteria form').ready(criteria_value);

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
                $('.user-search-result').html(response.result).show();
                user_searching = false;
                button.removeClass('loading');
            }
        }
    });
});

$('.problem-collaborators').ready(function(){
    if ($('input#id_public').is(':checked'))
        $('fieldset.user-search').hide();
    else
        $('fieldset.user-search').show();
});

$('.problem-collaborators').on('click', 'input#id_public', function(){
    if ($(this).is(':checked')) {
        $('fieldset.user-search').slideUp();
    } else {
        $('fieldset.user-search').slideDown();
    }
});

$('.problem-form').on('click', '.user-search-selected,.user-search-result a.username', function(e){
    e.preventDefault();
});

$('.top-bar').on('mouseenter', '.hover-li', function(){
    hover = $(this).data('hover');
    $(this).parent().find('.' + hover + ' a').addClass('hover');
});
$('.top-bar').on('mouseleave', '.hover-li', function(){
    hover = $(this).data('hover');
    $(this).parent().find('.' + hover + ' a').removeClass('hover');
});

$('.user-search-selected').on('click', '.collaborator-delete', function(e){
    e.preventDefault();
    var user_box = $(this).find('.user-box');
    if (user_box.data('username')) {
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: {
                'collaborator_delete': user_box.data('username'),
                'problem': problem_id
            },
            complete: function(xhr, data) {
                if (data == 'success') {
                    response = JSON.parse(xhr.responseText);
                    $('.user-search-selected').html(response.result);
                }
            }
        });
    }
});

$('.user-search-result').on('click', '.user-box', function(){
    if ($(this).data('username')) {
        $.ajax({
            url: '/ajax/',
            type: 'GET',
            data: {
                'collaborator_add': $(this).data('username'),
                'problem': problem_id
            },
            complete: function(xhr, data) {
                if (data == 'success') {
                    response = JSON.parse(xhr.responseText);
                    $('.user-search-selected').html(response.result);
                    $('.user-search-result').hide();
                    $('#id_user_search').val('');
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

$('.problem-tabs').on('click', '>a', function(e){
    /***
    Tab selection on the problem frontend.
    ***/
    e.preventDefault();
    window.location.hash = $(this).data('tab');
    $('.problem-tabs > a').removeClass('marked');
    $(this).addClass('marked');
    $('.problem-tab').stop().slideUp(200);
    $('.problem-' + $(this).data('tab')).stop().slideDown(200);
});

$('.problem-tabs').ready(function(){
    /***
    Actions related to hyperlinks for problem view
    ***/
    var tab;
    var obj;
    var match;
    // When accessing the URL directly to a tab
    r1 = /^#(criteria|ideas|alternatives|results)$/;
    r2 = /^#(criteria|idea|alternative)-([0-9]+)$/;
    if (window.location.hash.match(r1)) {
        match = r1.exec(window.location.hash);
        tab = match[1];
        obj = false;
    } else if (window.location.hash.match(r2)) {
        match = r2.exec(window.location.hash);
        if (match[1] == "criteria")
            tab = 'criteria';
        else if (match[1] == "idea")
            tab = 'ideas';
        else if (match[1] == "alternative")
            tab = 'alternatives';
        obj = tab + '-' + match[2];
    } else {
        tab = 'description';
        obj = false;
    }
    $('.problem-tabs').find('[data-tab="' + tab + '"]').trigger('click');
    $('.problem-tabs').find('[data-tab="' + tab + '"]').addClass('marked');
    $('.problem-tabs > div').height($('.problem-tabs').height());
    $('.problem-tab').stop().slideUp(200);
    $('.problem-' + tab).stop().slideDown(200, function(){
        if (obj)
            scrollTo('#' + obj);
        if (tab == 'alternatives') {
            for (var r in $('.range-slider')) {
                Foundation.libs.slider.reflow(r);
            }
        }
    });

});
if (window.location.hash.match(/^#(criteria|ideas|alternatives|results)$/)) {
    $('.problem-tabs').find('[data-tab="' + window.location.hash.replace('#', '') + '"]').trigger('click');
}

// When accessing the URL directly to an idea or comment in ProblemView

if (window.location.hash.match(/^#(idea|comment|criteria)-[0-9]+$/)) {
    var target = $(window.location.hash);
    target.highlight('green', 2000);
}

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

$(document).on('mouseenter', '.like', function(){
    $(this).addClass('highlighted');
});
$(document).on('mouseleave', '.like', function(){
    $(this).removeClass('highlighted');
});

$(document).on('click', '.idea-like', function(){
    /***
    Assign a vote to an idea.
    ***/
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

$(document).on('mouseup', '.range-slider', function(){
    /***
    Assign a value to an alternative counter.
    ***/
    var vote = $(this).parent();
    var counter = vote.find('.alternative-like-counter');
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'alternative_like': vote.data('alternative'),
            'value': counter.text()
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                vote.addClass('voted');
                counter.text(response.counter);
            }
        }
    });
});

$(document).on('click', '.comment-button', function(e){
    /***
    Show the comment form in the proper place for ideas and criteria.
    ***/
    e.preventDefault();
    var form = $('#comment-form');
    var new_form = form.clone();
    var obj;
    if ($(this).data('activity')) {
        var t;
        var types = ['problem', 'criteria', 'idea', 'alternative'];
        for (t in types) {
            if ($(this).data(types[t])) {
                target_type = types[t];
                target_id = $(this).data(types[t]);
                break;
            }
        }
        console.log(target_type, target_id);
        id = $(this).data('activity');
        new_form.find('input#id_' + target_type).val(target_id);
        obj = $('div#comment-form-activity-' + id);
    } else if ($(this).data('problem')) {
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
    console.log(obj, new_form);
    obj.html(new_form.html()).removeClass('hide');
});

// Comment form submit

$('.comment-form').on('submit', 'form', function(e){
    /***
    Submits a comment.
    ***/
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

$('.problem').on('click', 'a.show-problem-collaborators', function(e){
    c = $('.collaborators');
    if (c.is(':visible')) {
        $('.collaborators').stop().slideUp(200);
    } else {
        $('.collaborators').stop().slideDown(200);
    }
});

$(document).on('click', 'a.display-more', function(e){
    $(this).parents('.comment').hide();
    $(this).parents('.comments').find('.hidden').show();
    $(this).remove();
});

function toggle_delete(type, id) {
    /***
    Prepare the delete confirmation modal for a problem, idea, comment or
    criteria.
    ***/
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
    /***
    Add new alternative to problem.
    ***/
    if ($(this).attr('disabled') == 'disabled')
        return false;
    var button = $(this);
    $.ajax({
        url: '/ajax/',
        type: 'GET',
        data: {
            'new_alternative': 1,
            'problem': problem_id
        },
        complete: function(xhr, data) {
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                $('.new-alternative').after(response.html);
            }
        }
    });
});

var alternative_delete_modal = $('#alternative-delete-modal');
$(document).on('click', '.delete-alternative', function(){
    /***
    Pops the confirmation dialog to delete an alternative.
    ***/
    alternative_delete_modal.data('alternative', $(this).data('alternative'));
    alternative_delete_modal.foundation('reveal', 'open');
});
$(document).on('click', '.delete-alternative-confirm', function(){
    /***
    Confirms the deletion of an alternative and sends the ajax action for it.
    ***/
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

$(document).on('click', '.edit-alternative', function(){
    /***
    Shows the ideas modal to select them for alternatives.
    ***/
    var m = $('#alternative-edit');
    m.data('alternative', $(this).data('alternative'));
    m.data('idea', {});
    var name = $('.alternative-' + m.data('alternative')).
       find('.alternative-name');
    var name_field = m.find('#id_name');
    name_field.val(name.text());

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
    /***
    Select ideas in a modal.
    ***/
    var m = $('#alternative-edit');
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
$(document).on('click', '.alternative-save', function(){
    /***
    Saves the selected ideas in a modal.
    ***/
    var button = $(this);
    if (button.attr('disabled') == 'disabled')
        return false;
    button.attr('disabled', true);
    button.addClass('loading');
    var m = $('#alternative-edit');
    var alternative_id = m.data('alternative');
    var name = $('.alternative-' + alternative_id).
       find('.alternative-name');
    var name_field = m.find('#id_name');
    $.ajax({
        url: '/ajax/',
        type: 'POST',
        data: {
            'alternative_save': 1,
            'alternative': alternative_id,
            'idea': m.data('idea'),
            'name': name_field.val()
        },
        complete: function(xhr, data) {
            button.attr('disabled', false);
            button.removeClass('loading');
            if (data == 'success') {
                response = $.parseJSON(xhr.responseText);
                m.find('.holder').removeClass('error');
                m.find('small.error').remove();
                if (response.errors) {
                    for (var e in response.errors) {
                        m.find('#div_id_' + e).addClass('error');
                        m.find('#div_id_' + e).after('<small class="error">' + response.errors[e] + '</small>');
                    }
                    return false;
                }
                $('.alternative-' + alternative_id).replaceWith(response.html);
                m.foundation('reveal', 'close');
                // # Fix slider for dynamic contents
                Foundation.libs.slider.reflow($('.range-slider'));
            }
        }
    });
});

// Foundation

$(document).foundation();

})(jQuery);
