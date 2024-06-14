import http from 'k6/http';
import { sleep, check } from 'k6';

const targetUrl = __ENV.TARGET_URL;

export let options = {
    stages: [
        { duration: '1m', target: 100 },   // Ramp-up to 100 users
        { duration: '5m', target: 100 },   // Hold at 100 users
        { duration: '1m', target: 500 },   // Ramp-up to 500 users
        { duration: '5m', target: 500 },   // Hold at 500 users
        { duration: '1m', target: 1000 },  // Ramp-up to 1000 users
        { duration: '5m', target: 1000 },  // Hold at 1000 users
        { duration: '1m', target: 0 },     // Ramp-down to 0 users
    ],
};

export default function () {
    let res = http.get(`http://${targetUrl}/travel`);
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
    sleep(1);
}
