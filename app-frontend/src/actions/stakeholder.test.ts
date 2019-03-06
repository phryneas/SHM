import * as http from './http'
import { addStakeholder } from './stakeholder'

jest.mock('./http');

describe('Stakeholder Tests', () => {

    jest.mock('./http');

    it('adds a stakeholder', () => {
        const mockedDependency = <jest.Mock>http.postData;
        mockedDependency.mockReturnValueOnce(new Promise((resolve, reject) => {
            resolve(true);
        }));

        addStakeholder({
            projectId: 1,
            name: 'Bernd',
            company: 'Kika',

        })
    });

});