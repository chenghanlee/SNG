// The following function validates the login information

$(document).ready(function(){
	//listen for signup form submissions
	signupFormSubmit('#signup-form-topbar');
	signupFormSubmit('#signup-form-body');

	//listen for login form submissions
	loginFormSubmit('#login-form-topbar');
	loginFormSubmit('#login-form-body');

	$("#hybrid .modal-body .row #login-form-body").hide();
});

function loginFormSubmit(formId) {
	$(formId).submit(function(e){
		e.preventDefault();
		$('.login-form-error').remove();

		formData = $(formId).serialize();
		$.post('/login', formData, function(result){
			if(result.status == "success"){
				window.location = result.redirect;
			}
			else if(result.status == "error"){
				var selector = (formId == "#login-form-topbar") ? "#login .modal-body" : "#hybrid .modal-body #login-form";
				//displaying the appropriate error message
				$(selector).prepend(
					"<div class=\"alert-message error login-form-error\"><p>" + result.msg + "</p> </div>" 
				);
			}
		});
	});
}

function signupFormSubmit(formId){
	$(formId).submit(function(e){
		e.preventDefault();
		$('.help-inline').remove();
		
		formData = $(formId).serialize();
		$.post('/signup', formData, function(result){
			if(result.status == "success"){
				window.location = result.redirect;
			}
			else if(result.status == "error"){
				var base = (formId == "#signup-form-topbar") ? "#signup .modal-body " : "#hybrid .modal-body #signup-form " + formId + " ";
				var email_selector = base + "#email";
				var username_selector = base + "#username";
				var password_selector = base + "#password";
				
				//removing any prior error highlighted fields
				$(email_selector).removeClass("error");
				$(username_selector).removeClass("error");
				$(password_selector).removeClass("error");
				$('.help-block').remove();
				
				//displaying the appropriate error messages
				if(result.email_error !== undefined){
					$(email_selector).addClass("error");
					$(email_selector + " .input").append(
						"<span class=\"help-block\">" + result.email_error + "</span>"
					);
				}
					
				if(result.username_error !== undefined){
					$(username_selector).addClass("error");
					$(username_selector + " .input").append(
						"<span class=\"help-block\">" + result.username_error + "</span>"
					);
				}
			
				if(result.password_error !== undefined){
					$(password_selector).addClass("error");
					$(password_selector + " .input").append(
						"<span class=\"help-block\">" + result.password_error + "</span>"
					);
				}
			}
		});
	});
}

function showLoginForm(){
    $("#hybrid .modal-body .row #signup-tab").removeClass("active");
    $("#hybrid .modal-body .row #signup-form-body").hide();

	$("#hybrid .modal-body .row #login-tab").addClass("active");
	$("#hybrid .modal-body .row #login-form-body").show();
	$('.login-form-error').show();
}

function showSignupForm(){
	$("#hybrid .modal-body .row #signup-tab").addClass("active");
    $("#hybrid .modal-body .row #signup-form-body").show();

	$("#hybrid .modal-body .row #login-tab").removeClass("active");
	$("#hybrid .modal-body .row #login-form-body").hide();
	$('.login-form-error').hide();
}