setInterval(() => {
    if (isTokenExpired()) {
        Logout();
    }
}, 60000);

window.onload = function() {
    checkLoginStatus();
};

function checkLoginStatus() {
    const storedToken = localStorage.getItem('jwt');
    if (storedToken && !isTokenExpired()) {
        const isLoggedInText = document.getElementById('isLoggedInText');
        isLoggedInText.textContent = 'Logged In';
        LoadPageKeyList();
    } else {
        Logout();
    }
}

function enterKey() {
    var input = document.getElementById("input");
    var button = document.getElementById("button");

    input.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            button.click();
        }
    });
}

function DisplayCurrentUser() {
    const user_display = document.getElementById('currentUser');
    const username = document.getElementById('username').value;

    if (!localStorage.getItem('jwt')) {
        user_display.textContent = 'Logged Out';
    } else {
        user_display.textContent = username;
    }
}

setInterval(DisplayCurrentUser, 1000);

DisplayCurrentUser();

function LoadPageKeyList() {
    const keylistElement = document.getElementById('keylist');
    keylistElement.innerHTML = '';

    const pageLogin = document.getElementById('pageLogin');
    const pageCreate = document.getElementById('pageCreate');

    pageLogin.classList.add('hidden');
    pageCreate.classList.add('hidden');

    const pageList = document.getElementById('pageKeyList');
    pageList.classList.remove('hidden');
}

function LoadPageCreateKey() {
    const pageLogin = document.getElementById('pageLogin');
    const pageList = document.getElementById('pageKeyList');
    pageLogin.classList.add('hidden');
    pageList.classList.add('hidden');

    const pageCreate = document.getElementById('pageCreate');
    pageCreate.classList.remove('hidden');
}

function Logout() {
    localStorage.removeItem('jwt');
    localStorage.removeItem('jwt_exp');

    const isLoggedInText = document.getElementById('isLoggedInText');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    isLoggedInText.textContent = 'Not Logged In';
    usernameInput.value = '';
    passwordInput.value = '';

    const pageList = document.getElementById('pageKeyList');
    const pageCreate = document.getElementById('pageCreate');
    pageList.classList.add('hidden');
    pageCreate.classList.add('hidden');

    const pageLogin = document.getElementById('pageLogin');
    pageLogin.classList.remove('hidden');
}

function login() {
    const isLoggedInText = document.getElementById('isLoggedInText');
    const username = document.getElementById('username').value;
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

            LoadPageKeyList();
        })
        .catch(function(error) {
            console.error(error);
            isLoggedInText.classList.remove('hidden');
            isLoggedInText.textContent = "Invalid Username or Password";
        });
}

function showKeyList() {
    if (isTokenExpired()) {
        Logout();
        return;
    }

    const storedToken = localStorage.getItem('jwt');

    axios.get('http://127.0.0.1:5000/admin/keylist', {
        headers: {
            'Authorization': `Bearer ${storedToken}`
        }
    })
        .then(function(response) {
            DisplayKeyList(response.data.api_keys);
        })
        .catch(function(error) {
            console.log(error);
        });
}

function CreateKey() {
    if (isTokenExpired()) {
        Logout();
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
            LoadPageKeyList();
        })
        .catch(function(error) {
            newKeyElement.classList.remove('hidden')
            newKeyElement.textContent = 'Error creating API key. Please try again.';
        });
}

function DisplayKeyList(apiKeys) {
    const keylistElement = document.getElementById('keylist');
    keylistElement.innerHTML = '';

    const table = document.createElement('table');
    table.id = 'table';

    if (apiKeys.length === 0) {
        keylistElement.innerHTML = '<p>No API keys found.</p>';
        return;
    }

    const headerRow = document.createElement('tr');

    const headerCell1 = document.createElement('th');
    headerCell1.textContent = 'Creator';

    const headerCell2 = document.createElement('th');
    headerCell2.textContent = 'API Key';

    const headerCell3 = document.createElement('th');
    headerCell3.textContent = 'Actions';

    headerRow.appendChild(headerCell1);
    headerRow.appendChild(headerCell2);
    headerRow.appendChild(headerCell3);
    table.appendChild(headerRow);

    const username = document.getElementById('username').value


    apiKeys.forEach(api => {
        const row = document.createElement('tr');

        const cell1 = document.createElement('td');
        cell1.textContent = api.key_maker;

        const cell2 = document.createElement('td');
        cell2.textContent = api.api_key;

        const cell3 = document.createElement('td');

        if (api.key_maker === username) {
            const updateIcon = document.createElement('i');
            updateIcon.className = 'fas fa-edit';
            updateIcon.onclick = function() {
                update_key(api.api_key);
            };
            updateIcon.style.cursor = 'pointer';
            updateIcon.title = 'Update';

            const deleteIcon = document.createElement('i');
            deleteIcon.className = 'fas fa-trash';
            deleteIcon.onclick = function() {
                delete_key(api.api_key);
            };
            deleteIcon.style.cursor = 'pointer';
            deleteIcon.title = 'Delete';

            cell3.appendChild(updateIcon);
            cell3.appendChild(document.createTextNode(' '));
            cell3.appendChild(deleteIcon);
        }

        row.appendChild(cell1);
        row.appendChild(cell2);
        row.appendChild(cell3);
        table.appendChild(row);
    });

    keylistElement.appendChild(table);
}

function update_key(api_key) {
    console.log(api_key);
}

function delete_key(api_key) {
    console.log(api_key);
}

function isTokenExpired() {
    const expirationTime = localStorage.getItem('jwt_exp');
    return !expirationTime || Date.now() > expirationTime;
}
