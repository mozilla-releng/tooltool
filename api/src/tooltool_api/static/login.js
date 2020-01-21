import config from './config.mjs';

(function() {

function parseQuery(q) {
  const qs = q.replace('?', '').split('&');

  return qs.reduce((acc, curr) => {
    const [parameter, value] = curr.split('=');

    acc[parameter] = value;

    return acc;
  }, {});
}

window.login = {};
window.login.handle = function() {
  if (window.location.search) {
    const qs = parseQuery(window.location.search);

    if (qs.error) {
      alert("Failed to parse query string: " + qs.error);
      console.log("Failed to parse query string: " + qs.error);
    }
    else if (qs.state === '5') {
      $.ajax({
        url: config.taskclusterRootUrl + '/login/oauth/token',
        contentType: 'application/x-www-form-urlencoded',
        method: 'POST',
        data: {
          grant_type: 'authorization_code',
          code: qs.code,
          redirect_uri: config.redirectUri,
          client_id: config.clientId,
        },
        error: function(xhr, status, error) {
          alert("Login failed: " + error);
          console.log("Login failed: " + error);
        },
        success: function(data) {
          console.log("login succeeded");
          window.localStorage.setItem('auth', JSON.stringify(data))
          window.location = window.location.origin;
        }
      });
    }
  }
};

})();
