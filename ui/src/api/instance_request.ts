import { Cloud } from "../types";
import request from "./request";

export const CreateInstanceRequest = async (type: Cloud.Type, hostname: string, template_id: string, reason: string): Promise<{ detail: { msg: string } }> => {
    const response = await request(`/proxmox/$username/${type.toString()}-request/${hostname}`, { method: "POST", body: JSON.stringify({ template_id: template_id.toString(), reason }) });
    return response[1];
}

export const RespecInstanceRequest = async (hostname: string, type: Cloud.Type, detail: string): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/respec-request`, { method: "POST", body: JSON.stringify({ detail }) });
    return response[0] == 201;
}

export const ApproveInstanceRequest = async (username: string, hostname: string, type: Cloud.Type, token: string): Promise<{ detail: { msg: string } }> => {
    const response = await request(`/proxmox/${username}/${type.toString()}-request/${hostname}/approval?token=${token}`, { method: "POST" });
    return response[1]; 
}

export const DenyInstanceRequest = async (username: string, hostname: string, type: Cloud.Type, token: string): Promise<{ detail: { msg: string } }> => {
    const response = await request(`/proxmox/${username}/${type.toString()}-request/${hostname}/denial?token=${token}`, { method: "POST" });
    return response[1]; 
}
