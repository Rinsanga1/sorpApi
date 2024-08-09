import Helper from "./helperFunctions";

class LoadPage{

    LoadPageKeyList() {
        const keylistElement = document.getElementById('keylist');
        keylistElement.innerHTML = '';

        const pageLogin = document.getElementById('pageLogin');
        const pageCreate = document.getElementById('pageCreate');

        pageLogin.classList.add('hidden');
        pageCreate.classList.add('hidden');

        const pageList = document.getElementById('pageKeyList');
        pageList.classList.remove('hidden');
    }

    LoadPageCreateKey() {
        const pageLogin = document.getElementById('pageLogin');
        const pageList = document.getElementById('pageKeyList');
        pageLogin.classList.add('hidden');
        pageList.classList.add('hidden');

        const pageCreate = document.getElementById('pageCreate');
        pageCreate.classList.remove('hidden');
    }

    DisplayKeyList(apiKeys) {
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

}

export default new LoadPage();
