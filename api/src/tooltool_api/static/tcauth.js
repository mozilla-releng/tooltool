(function() {

window.tcauth = {};

window.tcauth.get_header = function(url, method) {
    var tc_auth = window.localStorage.getItem('tc_auth');

    try {
        tc_auth = JSON.parse(tc_auth);
    } catch(err) {
        tc_auth = null;
    }

    if (tc_auth == null) {
        return '';
    }

    if (tc_auth.credentials &&
        tc_auth.credentials.clientId &&
        tc_auth.credentials.accessToken) {

        var extData = null;
        if (tc_auth.credentials.certificate) {
            extData = new buffer.Buffer(JSON.stringify({
                certificate: JSON.parse(tc_auth.credentials.certificate)
            })).toString('base64');
        }

        var header = hawk.client.header(
            url,
            method || 'GET',
            {
                credentials: {
                    id: tc_auth.credentials.clientId,
                    key: tc_auth.credentials.accessToken,
                    algorithm: 'sha256'
                },
                ext: extData,
            }
        );
    };

    return header.field;
};

window.tcauth.setup = function(service, default_service_url) {
    var $login = $('#login');
    var $loggedin = $('#loggedin');
    var $logout= $('#logout');
    var $email = $('#email');
    var service_url = $('body').attr('data-' + service + '-url') || default_service_url;

    var auth = window.localStorage.getItem('auth');

    try {
        auth = JSON.parse(auth);
    } catch(err) {
        auth = null;
    }
    console.log(auth);
    if (auth != null && auth.access_token) {
        $.ajax({
            url: 'https://firefox-ci-tc.services.mozilla.com/login/oauth/credentials',
            async: false,
            headers: {
                Authorization: 'Bearer ' + auth.access_token,
                'Content-Type': 'application/json',
            },
            error: function(xhr, status, error) {
            },
            success: function(data, status, xhr) {
                $email.html('<span>' + data.credentials.clientId + '</span>' + '<span class="caret"></span/>');
                $login.toggleClass('hidden');
                $loggedin.toggleClass('hidden');
                window.localStorage.setItem('tc_auth', JSON.stringify(data));
                $.ajax({
                    url: service_url + '/init',
                    async: false,
                    beforeSend: function (xhr, config) {
                        xhr.setRequestHeader("Authorization", tcauth.get_header(config.url, config.method));
                    },
                    success: function(data, status, xhr) {
                        angular.module('initial_data', []).constant('initial_data', data || {});
                    }
                });
            }
        });
    } else {
        angular.module('initial_data', []).constant('initial_data', {});
    }

    $login.on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var url = 'https://firefox-ci-tc.services.mozilla.com/login/oauth/authorize?client_id=releng-tooltool-localdev&redirect_uri=https%3A%2F%2Flocalhost%3A8010%2Fstatic%2Flogin.html&response_type=code&scope=project%3Areleng%3Aservices%2Ftooltool%2F*&state=5&expires=5%20minutes';
        window.location = url;
    });

    $logout.on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        window.localStorage.removeItem('auth');
        window.localStorage.removeItem('tc_auth');
        window.location.reload();
    });
};

})();
