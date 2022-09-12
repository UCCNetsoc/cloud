import { Cloud } from "../types";
import request from "./request";

export const GetInstances = async (type: Cloud.Type): Promise<Map<string, Cloud.Instance> | null> => {
    const response = await request(`/proxmox/$username/${type.toString()}`, { method: "GET" });
    return response[1];
};

export const DeleteInstance = async (hostname: string, type: Cloud.Type): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}`, { method: "DELETE" });
    return response[0] === 200;
}

export const StartInstance = async (hostname: string, type: Cloud.Type): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/start`, { method: "POST" });
    return response[0] === 201;
}

export const StopInstance = async (hostname: string, type: Cloud.Type): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/stop`, { method: "POST" });
    return response[0] === 200;
}

export const ShutdownInstance = async (hostname: string, type: Cloud.Type): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/shutdown`, { method: "POST" });
    return response[0] === 200;
}

export const ResetRootPassword = async (hostname: string, type: Cloud.Type): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/reset-root-user`, { method: "POST" });
    return response[0] === 200;
}

export const MarkInstanceActive = async (hostname: string, type: Cloud.Type): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/active`, { method: "POST" });
    return response[0] === 201;
}

export const AddInternetPort = async (hostname: string, type: Cloud.Type, internal_port: number, external_port: number): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/port/${external_port}/${internal_port}`, { method: "POST" });
    return response[0] === 200 || response[0] === 201;
}

export const FindRandomPort = async (hostname: string, type: Cloud.Type): Promise<number | null> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/free-external-port`, { method: "GET" });
    return response[1];
}

export const RemoveInternetPort = async (hostname: string, type: Cloud.Type, external_port: number): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/port/${external_port}`, { method: "DELETE" });
    return response[0] === 200;
}

export const AddInstanceVhost = async (hostname: string, type: Cloud.Type, vhost: string): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/vhost/${vhost}`, { method: "POST" });
    return response[0] === 200 || response[0] === 201;
}

export const RemoveInstanceVhost = async (hostname: string, type: Cloud.Type, vhost: string): Promise<boolean> => {
    const response = await request(`/proxmox/$username/${type.toString()}/${hostname}/vhost/${vhost}`, { method: "Delete" });
    return response[0] === 200;
}
