import { Cloud } from "../types";
import request from "./request";

export const GetTemplates = async (type: Cloud.Type): Promise<Map<string, Cloud.Template> | null> => {
    const response = await request(`/proxmox/$username/${type.toString()}-templates`, { method: "GET" });
    // add hostname as an optional value so it can be used in clientside request
    for (let id in response[1]) {
        response[1][id].hostname = id
    }
    return response[1];
};

export const GetTemplateById = async (type: Cloud.Type, templateId: string): Promise<Cloud.Template> => {
    const response = await request(`/proxmox/$username/${type.toString()}-template/${templateId}`, { method: "GET" })
    return response[1]
};

export const GetAllTemplates = async (): Promise<Cloud.Template[]> => {
    const lxc_templates = await GetTemplates(Cloud.Type.LXC)
    const vps_templates = await GetTemplates(Cloud.Type.VPS)

    return [...lxc_templates ? Object.values(lxc_templates) : [], ...vps_templates ? Object.values(vps_templates) : []];
};

export const GetLXCTemplates = async (): Promise<Cloud.Template[]> => {
    const lxc_templates = await GetTemplates(Cloud.Type.LXC)
    return [...lxc_templates ? Object.values(lxc_templates) : []]
};

export const GetVPSTemplates = async (): Promise<Cloud.Template[]> => {
    const vps_templates = await GetTemplates(Cloud.Type.VPS)
    return [...vps_templates ? Object.values(vps_templates) : []]
};
