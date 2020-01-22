import config from './config.mjs';

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
    var tc_auth = window.localStorage.getItem('tc_auth');

    function handleLoggedIn(data) {
        $email.html('<span>' + data.credentials.clientId + '</span>' + '<span class="caret"></span/>');
        $login.toggleClass('hidden');
        $loggedin.toggleClass('hidden');
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

    try {
        tc_auth = JSON.parse(tc_auth);
    } catch(err) {
        tc_auth = null;
    }

    // If we already have credentials, see if they're still valid
    if (tc_auth) {
        var expires = moment(tc_auth.expires);
        var now = moment();

        // If they are, great!
        if (expires > now) {
            handleLoggedIn(tc_auth);
        // If not, force user reauth.
        // It may be possible to do this in the background, but I haven't figured out how
        } else {
            window.localStorage.removeItem('auth');
            window.localStorage.removeItem('tc_auth');
        }
    }
    else {
        // If there are no credentials, check for an access code (which is what
        // should be present after the user is redirected back from the auth
        // flow)
        try {
            auth = JSON.parse(auth);
        } catch(err) {
            auth = null;
        }
        // If we have one, get some credentials!
        if (auth != null && auth.access_token) {
            $.ajax({
                url: config.taskclusterRootUrl + '/login/oauth/credentials',
                async: false,
                headers: {
                    Authorization: 'Bearer ' + auth.access_token,
                    'Content-Type': 'application/json',
                },
                error: function(xhr, status, error) {
                    alert("Failed to get credentials: " + error);
                    console.log("Failed to get credentials: " + error);
                },
                success: function(data, status, xhr) {
                    window.localStorage.setItem('tc_auth', JSON.stringify(data));
                    handleLoggedIn(data);
                }
            });
        } else {
            angular.module('initial_data', []).constant('initial_data', {});
        }
    }

    $login.on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var url = config.taskclusterRootUrl + '/login/oauth/authorize?client_id=' + config.clientId + '&redirect_uri=' + config.redirectUri + '&response_type=code&scope=' + config.scope + '&state=5&expires=5%20minutes';
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
