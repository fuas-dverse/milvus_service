import http from 'k6/http';
import { sleep, check } from 'k6';

const targetUrl = __ENV.EXTERNAL_IP;

export let options = {
    stages: [
        { duration: '10s', target: 10 }, // ramp up to 10 users over 10 seconds
        { duration: '1m', target: 100 }, // stay at 10 users for 1 minute
        { duration: '10s', target: 0 }, // ramp down to 0 users over 10 seconds
    ],
};

export default function () {
    let res = http.get(`${targetUrl}/travel`);
    check(res, {
        'is status 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(1); // wait for 1 second before the next iteration
}