import { Cloud } from "../types";
import request from "./request";

export const GetVhostRequirements = async (): Promise<Cloud.VHostRequirements> => {
    const response = await request(`/proxmox/vhost-requirements`, { method: "GET" }, true);
    return response[1];
};

export const AddVhost = async (type: Cloud.Type, hostname: string, domain: string, port: number, https: boolean): Promise<number> => {
    const response = await request(`/proxmox/$username/${type}/${hostname}/vhost/${domain}`, { method: "POST", body: JSON.stringify({ port: port, https: https }) }, true);
    return response[0];
};

export const DeleteVhost = async (type: Cloud.Type, hostname: string, domain: string): Promise<number> => {
    const response = await request(`/proxmox/$username/${type}/${hostname}/vhost/${domain}`, { method: "DELETE" }, true);
    return response[0];
};

export const GetFreePort = async (type: Cloud.Type, hostname: string): Promise<number> => {
    const response = await request(`/proxmox/$username/${type}/${hostname}/free-external-port`, { method: "GET" }, true);
    return response[1];
};

export const AddInstancePort = async (type: Cloud.Type, hostname: string, external_port: number, internal_port: number): Promise<number> => {
    const response = await request(`/proxmox/$username/${type}/${hostname}/port/${external_port}/${internal_port}`, { method: "POST" }, true);
    return response[0];
};
