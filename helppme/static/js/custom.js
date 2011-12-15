// The following function validates the login information

function getCookie(name){
    var cookie_array, nameEQ, value, _i, _len;
    nameEQ = name + "=";
    cookie_array = document.cookie.split(';');
    for (_i = 0, _len = cookie_array.length; _i < _len; _i++) {
        value = cookie_array[_i];
        while (value.charAt(0) === ' ') {
            value = value.substring(1, value.length);
        }
        if (value.indexOf(nameEQ) === 0) {
            return value.substring(nameEQ.length, value.length);
        }
    }
}

function setCookie(name, value, days) {
    var date, expires;
    if (days) {
        date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toGMTString();
    } else {
        expires = "";
    }
    document.cookie = name + "=" + value + expires + "; path=/";
    return document.cookie;
}

function lessSidebar(){
    $sidebar = $("ul#category_filter");
    $less = $sidebar.children("#less");
    $more = $sidebar.children("#more");
    $categories = $sidebar.children("li");
    $less.hide();
    $more.show();
    $categories.filter(":gt(5)").not("#more, .selected").slideUp("100");
    setCookie('expandSidebar', 'False');
}

function deleDeal(deal_id, slideUp){
    var data = {
        "deal_id": deal_id,
        "action": 'delete'
    };
    $.post('/deals/do_action/', data, function(result){
        if(result.status == "success"){
            if (slideUp == "True"){
                $("#"+deal_id).slideUp('100');
            }
        }
        else if (result.status == "error" && result.message == "user not logged in"){
            $("#hybrid").modal("show");
        }  
    });
}

function editDeal(deal_id){
    var deal_description = $(".span-deal .description");
    var text = deal_description.find('.details');
    var userActions = deal_description.find('.deal-user-actions');
    var socialNetworkButtons = deal_description.find('#social-network-buttons');
    var editForm = deal_description.find('.edit');
    text.hide();
    userActions.hide();
    socialNetworkButtons.hide();
    editForm.show();

    var $formId = $("#".concat(deal_id)); 
    $formId.submit(function(e){
        e.preventDefault();
        $("#edit-button").addClass("disabled");

        var path = "/deals/".concat(deal_id, "/edit/");
        var editedText = editForm.find('textarea#description').val();
        var data ={'description': editedText};
        $.post(path, data, function(result){
            if (result.status == "success"){
                var converter = new Markdown.Converter();
                var editedHTML = converter.makeHtml(editedText);
                text.html(editedHTML);
                text.append("<br /><p><em>edited now</em></p>");
                text.show();
                userActions.show();
                editForm.hide();
            }
            else if(result.status == "error"){
                updateInputField(editForm, "error", result.description_error );
            }
        });
    });
}

function cancelEdit(){
    var deal_description = $(".span-deal .description");
    var text = deal_description.find('.details');
    var userActions = deal_description.find('.deal-user-actions');
    var socialNetworkButtons = deal_description.find('#social-network-buttons');
    var editForm = deal_description.find('.edit');
    text.show();
    userActions.show();
    socialNetworkButtons.show();
    editForm.hide();
}

function flagDeal(deal_id){
    var data = {
        "deal_id": deal_id,
        "action": "flag"
    };

    $.post('/deals/do_action/', data, function(result){
        if(result.status == "success"){
             var $selector = $(".user-actions-2").find(".dropdown-menu").find("#flag");
            $selector.find("a").remove("a").end().addClass("not-available").text("Flag for spam");
        }
        else if (result.status == "error" && result.message == "user not logged in"){
            $("#hybrid").modal("show");
        } 
    }); 
}

function saveDeal(deal_id){
    var data = {
        "deal_id": deal_id,
        "action": 'save'
    };
    $.post('/deals/do_action/', data, function(result){
        if(result.status == "success"){
            var $selector = $(".user-actions-2").find(".dropdown-menu").find("#bookmark");
            $selector.find("a").remove("a").end().addClass("not-available").text("Bookmark");
        }
        else if (result.status == "error" && result.message == "user not logged in"){
            $("#hybrid").modal("show");
        } 
    });
}

function likeDeal(deal_id){
    var data = {
        "deal_id": deal_id,
        "action": "vote"
    };

    $.post('/deals/do_action/', data, function(result){
        if(result.status == "success"){
            var $deal = $('#'+deal_id);
            // incrementing the deal's number of likes
            var numLikes = $deal.find(".description").find('#num-likes');
            var number = numLikes.text();
            number = parseInt(number, 10) + 1;
            numLikes.parent().fadeOut('10', function(){
                numLikes.text(number).parent().fadeIn('10');
            });
            // removing the 'a' tag from the 'like' link, so the user can't click
            // on the link again
            $deal.find(".user-actions-2").find("#like").find("a").addClass('not-available-2').removeAttr("onclick").removeAttr("href");
            // var $like_link = $deal.find(".user-actions-2").find("#like");
            // $like_link.find("a").addClass('not-available-2').removeAttr("onclick").removeAttr("href");
        }
        else if (result.status == "error" && result.message == "user not logged in"){
            $("#hybrid").modal("show");
        } 
    });
}

function cancelFormSubmit(){
    var previousPage = document.referrer;
    var redirect = "http://127.0.0.1:5000";
    if (previousPage.indexOf("http://127.0.0.1:5000") != -1){
        redirect = previousPage;
    }
    window.location = redirect;
}

function dealFormSubmit(formId){
    $(formId).submit(function(e) {
        e.preventDefault();
        $('#deal-submit-button').addClass('disabled');

        formData = $(formId).serialize();
        $.post('/deals/post/', formData, function(result) {
            if (result.status == "success") {
                window.location = result.redirect;
            }
            else if (result.status == "error"){
                var dealForm = $(formId);
                var title = dealForm.find("#title");
                var location = dealForm.find("#location");
                var category = dealForm.find("#category");
                var description = dealForm.find("#description");

                //removing any prior error highlighted fields
                title.removeClass("error").removeClass("success");
                location.removeClass("error").removeClass("success");
                category.removeClass("error").removeClass("success");
                description.removeClass("error").removeClass("success");
                $('.help-block').remove();

                if (result.title_error !== undefined) {
                    updateInputField(title, "error", result.title_error);
                }
                else{
                    updateInputField(title, "success", "Ok!");   
                }

                if (result.location_error !== undefined) {
                    updateInputField(location, "error", result.location_error);
                }
                else{
                    updateInputField(location, "success", "Ok!");
                }

                if (result.category_error !== undefined) {
                    updateInputField(category, "error", result.category_error);
                }
                else{
                    updateInputField(category, "success", "Ok!");
                }

                if (result.description_error !== undefined) {
                    updateInputField(description, "error", result.description_error);
                }
                else{
                    updateInputField(description, "success", "Ok!");
                }
            }
        });
    });
}
function loginFormSubmit(formId) {
    $(formId).submit(function(e) {
        e.preventDefault();
        $('input #login-button').addClass('disabled');
        $('.login-form-error').remove();

        formData = $(formId).serialize();
        $.post('/user/login', formData, function(result) {
            if (result.status == "success") {
                window.location = result.redirect;
            }
            else if (result.status == "error") {
                var selector = (formId == "#login-form-topbar") ? "#login .modal-body" : "#hybrid .modal-body #login-form";
                //displaying the appropriate error message
                $(selector).prepend("<div class=\"alert-message block-message error login-form-error\"><p>" + result.msg + "</p> </div>");
            }
        });
    });
}

function signupFormSubmit(formId) {
    $(formId).submit(function(e) {
        e.preventDefault();
        $('.help-inline').remove();
        $('input #signup-button').addClass('disabled');

        formData = $(formId).serialize();
        $.post('/user/signup', formData, function(result) {
            if (result.status == "success") {
                window.location = result.redirect;
            }
            else if (result.status == "error") {
                var signupForm = $(formId);
                var email = signupForm.find("#email");
                var username = signupForm.find("#username");
                var password = signupForm.find("#password");

                //removing any prior error highlighted fields
                email.removeClass("error");
                username.removeClass("error");
                password.removeClass("error");
                $('.help-block').remove();

                //displaying the appropriate error messages
                if (result.email_error !== undefined) {
                    updateInputField(email, "error", result.email_error);
                }
                else{
                    updateInputField(email, "success", "Looks good!");   
                }

                if (result.username_error !== undefined) {
                    updateInputField(username, "error", result.username_error);
                }
                else{
                    updateInputField(username, "success", "Nice username!");
                }

                if (result.password_error !== undefined) {
                    updateInputField(password, "error", result.password_error);
                }
                else{
                    updateInputField(password, "success", "Good password!");
                }
            }
        });
    });
}

function updateInputField(selector, status, message){
    if (status == "error"){
        selector.addClass("error");
    }
    else if (status == "success"){
        selector.addClass("success");
    }
    selector.find(".input").append("<span class=\"help-block\">" + message + "</span>");
}

function showForm(formType) {
    selector = $("#hybrid .modal-body .row");
    if (formType == 'login'){
        selector.find('#signup-tab').removeClass("active").end().find("#signup-form-body").hide();
        selector.find('#login-tab').addClass("active").end().find("#login-form-body").show();
        $('.login-form-error').show();
    }
    else if (formType == 'signUp'){
        selector.find('#signup-tab').addClass("active").end().find("#signup-form-body").show();
        selector.find('#login-tab').removeClass("active").end().find("#login-form-body").hide();
        $('.login-form-error').hide();
    }
}

function showForgotPasswordForm(){
    loginForm = $('#hybrid');
    loginForm.modal('hide');

    selector = $("#forgot-password");
    selector.modal('show');    
}

function hideForgotPasswodForm(showHybridForm){
    selector = $("#forgot-password");
    selector.modal('hide');   
    if(showHybridForm === true){
        loginForm = $('#hybrid');
        loginForm.modal('show');
    }
}

function passwordRestSubmit(formId){
    $(formId).submit(function(e) {
        e.preventDefault();
        formData = $(formId).serialize();
        $.post('/user/forgot_password/', formData, function(result) {
            var selector = $('#forgot-password').find('.modal-body');
            var email = selector.find("#forgot-password-form").find("#email");                
            email.removeClass("error");

            if (result.status == "success"){
                selector.find('.input').remove().end().find("#cancel-password-reset-button").remove();
                selector.find('label').text("Done. We will send you an email shortly.");
                selector.find('#password-reset-button').attr("value", "Close").attr("onclick", "hideForgotPasswodForm(false); return false;");
            }
            else if (result.status == "error"){
                updateInputField(email, "error", result.email_error);
            }
        });
    });
}

$(document).ready(function() {
    /* 
        sidebar animations 
    */
    var expandSidebar = getCookie('expandSidebar');
    $sidebar = $("#category_filter");
    $less = $sidebar.children("#less");
    $more = $sidebar.children("#more");
    $categories = $sidebar.children('li');
     
    //if cookie says to expand sidebar, show all categories and hide 'more'
    if (expandSidebar == "True"){
        $more.hide();
    }
    //if cookie says don't expand sidebar, hide everthing below the 5th category and show 'more'
    else{
        $categories.filter(":gt(5)").not("#more, .selected").hide();
    }
    //setup a callback function whenever the link 'more' is clicked
    $more.click(function(){
        $categories.slideDown("100");
        $more.hide();
        setCookie("expandSidebar", "True");
    });

    /*
        form submissions
    */
    //listen for form submissions
    signupFormSubmit('#signup-form-topbar');
    signupFormSubmit('#signup-form-body');
    loginFormSubmit('#login-form-topbar');
    loginFormSubmit('#login-form-body');
    dealFormSubmit('#deal-submit-form');
    passwordRestSubmit("#forgot-password-form");

    //configure popup signup/login/forgot form to enable backdrop and listening to key presses
    $("#hybrid").modal({
        backdrop: true,
        keyboard: true
    });

    $("#forgot-password").modal({
        backdrop: true,
        keyboard: true
    });

    // set recover password modal to show login modal on close
    // $('#forgot-password').bind('hidden', function () {
    //     showForm('login');
    //     loginForm = $('#hybrid');
    //     loginForm.modal('show');
    // });

    //make signUp for the default form to showup
    showForm('signUp');
});