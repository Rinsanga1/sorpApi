import loadPage from "./loadPage";


class Helper {

    isTokenExpired() {
        const expirationTime = localStorage.getItem('jwt_exp');
        return !expirationTime || Date.now() > expirationTime;
    }

    DisplayCurrentUser() {
        const user_display = document.getElementById('currentUser');
        const username = document.getElementById('username').value;

        if (!localStorage.getItem('jwt')) {
            user_display.textContent = 'Logged Out';
        } else {
            user_display.textContent = username;
        }
    }

    Logout() {
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

}

export default new Helper();
