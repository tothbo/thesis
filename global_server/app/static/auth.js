function sleep (time){return new Promise((resolve) => setTimeout(resolve, time))}
(() => {
    'use strict'
  
    const forms = document.querySelectorAll('.needs-validation')

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault()
            event.stopPropagation()
            $('#formControlInputEmailFeedback')[0].innerHTML = 'please enter a valid e-mail address';
            $('#formControlInputEmail')[0].setCustomValidity('');
            $('#formControlInputPassFeedback')[0].innerHTML = 'please enter a password';
            $('#formControlInputPass')[0].setCustomValidity('');
            let dt = {
                username: $('#formControlInputEmail')[0].value,
                password: $('#formControlInputPass')[0].value
            }
            if (form.checkValidity()) {
                $.ajax({
                    url: '/token',
                    type: 'POST',
                    contentType: 'application/x-www-form-urlencoded; charset=UTF-8',
                    data: $.param(dt),
                    success: function(response) {
                        console.log("OK");
                        $('#login')[0].innerHTML = '<span class="material-symbols-outlined">verified_user</span>';
                        sleep(3000).then(() => {window.location.href = '/';});
                    },
                    error: function(xhr, status, error) {
                        console.error('Error:', xhr.responseText);
                        $('#formControlInputEmailFeedback')[0].innerHTML = 'invalid username and/or password';
                        $('#formControlInputEmail')[0].setCustomValidity('a');
                        $('#formControlInputPassFeedback')[0].innerHTML = ' ';
                        $('#formControlInputPass')[0].setCustomValidity('b');
                    }
                });
            }
            form.classList.add('was-validated');
        }, false)
    })
})()