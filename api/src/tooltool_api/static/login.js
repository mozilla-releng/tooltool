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
      console.log("fail!");
    }
    else if (qs.state === '5') {
      $.ajax({
        url: 'https://firefox-ci-tc.services.mozilla.com/login/oauth/token',
        contentType: 'application/x-www-form-urlencoded',
        method: 'POST',
        data: {
          grant_type: 'authorization_code',
          grant_type: 'authorization_code',
          code: qs.code,
          redirect_uri: 'https://localhost:8010/static/login.html',
          client_id: 'releng-tooltool-localdev',
        },
        error: function(xhr, status, error) {
          console.log("login failed");
          console.log(error);
        },
        success: function(data) {
          console.log("login succeeded");
          window.localStorage.setItem('auth', JSON.stringify(data))
          window.location = window.location.origin;
        }
      });
    }
  }
}

})();
