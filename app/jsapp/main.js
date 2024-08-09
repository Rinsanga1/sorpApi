import Helper from "./helperFunctions";
import loadPage from "./loadPage";


window.onload = function() {
    checkLoginStatus();
};

setInterval(() => {
    if (Helper.isTokenExpired()) {
        Helper.Logout();
    }
}, 60000);

setInterval(Helper.DisplayCurrentUser, 1000);

Helper.DisplayCurrentUser();

function checkLoginStatus() {
    const storedToken = localStorage.getItem('jwt');
    if (storedToken && !Helper.isTokenExpired()) {
        const isLoggedInText = document.getElementById('isLoggedInText');
        isLoggedInText.textContent = 'Logged In';
        loadPage.LoadPageKeyList();
    } else {
        Helper.Logout();
    }
}

function login() {
    const isLoggedInText = document.getElementById('isLoggedInText');
    const username = document.getElementById('uaername').value;
    const password = document.getElementById('password').value;

    axios.post('http://127.0.0.1:5000/admin/login', {
        user: username,
        pw: password
    })
        .then(function(response) {
            const token = response.data['access token'];
            isLoggedInText.textContent = 'Logged In';

            localStorage.setItem('jwt', token);

            const decodedToken = JSON.parse(atob(token.split('.')[1]));
            const expirationTime = decodedToken.exp * 1000;
            localStorage.setItem('jwt_exp', expirationTime);

            loadPage.LoadPageKeyList();
        })
        .catch(function(error) {
            console.error(error);
            isLoggedInText.classList.remove('hidden');
            isLoggedInText.textContent = "Invalid Username or Password";
        });
}

function showKeyList() {
    if (Helper.isTokenExpired()) {
        Helper.Logout();
        return;
    }

    const storedToken = localStorage.getItem('jwt');

    axios.get('http://127.0.0.1:5000/admin/keylist', {
        headers: {
            'Authorization': `Bearer ${storedToken}`
        }
    })
        .then(function(response) {
            loadPage.DisplayKeyList(response.data.api_keys);
        })
        .catch(function(error) {
            console.log(error);
        });
}


function CreateKey() {
    if (Helper.isTokenExpired()) {
        Helper.Logout();
        return;
    }

    const newKeyElement = document.getElementById('showKey');
    newKeyElement.innerHTML = '';
    const newKey = document.getElementById('newKey').value;
    const storedToken = localStorage.getItem('jwt');

    axios.post('http://127.0.0.1:5000/admin/apikey', {
        new_api_key: newKey
    }, {
        headers: {
            'Authorization': `Bearer ${storedToken}`
        }
    })
        .then(function(response) {
            console.log(response);
            if (response.data['error'] == '') {
                newKeyElement.classList.remove('hidden')
                newKeyElement.textContent = 'Error creating API key. Please try again.';
            }
            loadPage.LoadPageKeyList();
        })
        .catch(function(error) {
            newKeyElement.classList.remove('hidden')
            newKeyElement.textContent = 'Error creating API key. Please try again.';
        });
}

function update_key(id) {
    console.log(id);
}

function delete_key(id) {
    console.log(id);
}
