const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

async function getCsrfToken(baseUrl) {
    const response = await fetch(
        baseUrl + '/api/common/auth/csrftoken/', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });
    const responseJSON = await response.json();
    return responseJSON['csrftoken'];
}

const getToken = async (baseUrl, user, password) => {
    const csrfToken = await getCsrfToken(baseUrl);

    const payload = {
        "username": user,
        "password": password
    };
    const response = await fetch(
        baseUrl + '/api/common/auth/authtoken/',
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload)
        }
    )
    if (response.status !== 200) {
        throw new Error('failed to login')
    }
    const json = await response.json();
    return json['token'];
};

beforeEach(async () => {
    const baseUrl = "http://skipper.test.local:8000";
    const token = await getToken("http://skipper.test.local:8000", "admin", "admin");

    const dataSeriesName = 'myds' + process.env.JEST_WORKER_ID;

    const response = await fetch(
        baseUrl + '/api/dataseries/by-external-id/dataseries/' + dataSeriesName + '/',
        {
            method: 'DELETE',
            headers: {
                'Authorization': `Token ${token}`
            }
        }
    )
    if(response.status > 300 && response.status != 404) {
        throw new Error('failed to clean up old dataseries')
    }

    const newDSResponse = await fetch(
        baseUrl + '/api/dataseries/dataseries/',
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`
            },
            body: JSON.stringify({
                "name": dataSeriesName,
                "external_id": dataSeriesName,
                "backend": "DYNAMIC_SQL_NO_HISTORY"
            })
        }
    )
    expect(newDSResponse.status).toBe(201);

    const dataSeriesObj = await newDSResponse.json();
    
    const fileFactResponse = await fetch(
        dataSeriesObj["file_facts"],
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`
            },
            body: JSON.stringify({
                "name": "my_file",
                "external_id": "my_file",
                "optional": false
            })
        }
    )
    expect(fileFactResponse.status).toBe(201);
})

afterEach(() => {
    // noop
})

test("test file upload with axios single", async () => {
    const baseUrl = "http://skipper.test.local:8000";
    const token = await getToken("http://skipper.test.local:8000", "admin", "admin");

    const dataSeriesName = 'myds' + process.env.JEST_WORKER_ID;

    const formData = new FormData();
    formData.append('external_id', 'external_id');
    formData.append('payload.my_file', fs.createReadStream(__dirname + '/some_test_file.txt'), 'some_test_file.txt')

    const response = await axios.post(
        baseUrl + '/api/dataseries/by-external-id/dataseries/' + dataSeriesName + '/datapoint/',
        formData,
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Token ${token}`
            }
        }
    )
    expect(response.status).toBe(201);
});

test("test file upload with axios batch", async () => {
    const baseUrl = "http://skipper.test.local:8000";
    const token = await getToken("http://skipper.test.local:8000", "admin", "admin");

    const dataSeriesName = 'myds' + process.env.JEST_WORKER_ID;

    const formData = new FormData();
    formData.append('batch-1.external_id', 'external_id');
    formData.append('batch-1.payload.my_file', fs.createReadStream(__dirname + '/some_test_file.txt'), 'some_test_file.txt');
    formData.append('batch-2.external_id', 'external_id2');
    formData.append('batch-2.payload.my_file', fs.createReadStream(__dirname + '/some_test_file.txt'), 'some_test_file.txt')

    const response = await axios.post(
        baseUrl + '/api/dataseries/by-external-id/dataseries/' + dataSeriesName + '/bulk/datapoint/',
        formData,
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Token ${token}`
            },
        }
    )
    expect(response.status).toBe(201);
});