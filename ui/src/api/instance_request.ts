import { Cloud } from "../types";
import request from "./request";

export const RespecInstanceRequest = async (hostname: string, type: Cloud.Type, detail: string): Promise<boolean> => {
    const response = await request(`/$username/${type.toString()}/${hostname}/respec-request`, { method: "POST", body: JSON.stringify({ detail: detail }) });
    return response[0] == 201;
}


