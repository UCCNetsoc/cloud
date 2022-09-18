import request from "./request";


export const IsLoggedIn = async (): Promise<boolean> => {
    const response = await request(`/accounts/`, { method: "GET" });
    return response[0] === 200;
};
