import { Cloud } from "../types";
import request from "./request";

export const IsLoggedIn = async (): Promise<boolean> => {
    const response = await request(`/accounts/`, { method: "GET" });
    return response[0] === 200;
};

export const SignupUccStudent = async (username: string, email: string): Promise<Cloud.GenericResponse> => {
    const response = await request("/signups/ucc-student", { method: "POST", body: JSON.stringify({ email, username }) })
    return response[1]
}

export const SendVerificationEmail = async (username_or_email: string, captchaToken: string): Promise<Cloud.GenericResponse> => {
    const response = await request(`/accounts/${username_or_email}/verification-email`, { body: JSON.stringify({ captcha: captchaToken }), method: "POST" })
    return response[1]
}

export const VerifyAccountSignup = async (username_or_email: string, token: string, password: string): Promise<Cloud.GenericResponse> => {
    const response = await request(`/accounts/${username_or_email}/verification`, { method: "POST", body: JSON.stringify({ serialized_verification: { token }, password }) })
    return response[1]
}
