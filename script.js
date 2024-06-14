import http from 'k6/http';
import { sleep, check } from 'k6';

const targetUrl = __ENV.TARGET_URL;

export let options = {
    stages: [
        { duration: '30s', target: 2500 },
        { duration: '30s', target: 2500 },
        { duration: '30s', target: 5000 },
        { duration: '30s', target: 5000 },
        { duration: '30s', target: 10000 },
        { duration: '30s', target: 10000 },
        { duration: '30s', target: 0 },
    ],
};

export default function () {
    let res = http.get(`http://${targetUrl}/travel`);
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
    sleep(1);
}