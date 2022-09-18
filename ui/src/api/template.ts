import { Cloud } from "../types";
import request from "./request";

export const GetTemplates = async (type: Cloud.Type): Promise<Map<string, Cloud.Template> | null> => {
    const response = await request(`/proxmox/$username/${type.toString()}-templates`, { method: "GET" });
    return response[1];
};

export const GetAllTemplates = async (): Promise<Cloud.Template[]> => {
    const lxc_templates = await GetTemplates(Cloud.Type.LXC)
    const vps_templates = await GetTemplates(Cloud.Type.VPS)

    return [...lxc_templates ? Object.values(lxc_templates) : [], ...vps_templates ? Object.values(vps_templates) : []];
}