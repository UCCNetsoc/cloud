export module Cloud {
  export interface Instance {
    type: Type;
    node: string;
    id: number;
    hostname: string;
    fqdn: string;
    specs: Specs;
    active: boolean;
    inactivity_shutdown_date: string;
    inactivity_deletion_date: string;
    metadata: Metadata;
    remarks: string[];
    status: Status;
    uptime?: number;
    mem: number;
    disk: number;
  }

  export enum Status {
    NotApplicable = 'n/a',
    Stopped = 'Stopped',
    Running = 'Running'
  }

  export enum Type {
    LXC = 'lxc',
    VPS = 'vps',
  }

  export interface Specs {
    cores: number;
    disk_space: number;
    memory: number;
    swap: number;
  }

  export interface Metadata {
    groups: string[];
    host_vars: { [key: string]: string };
    owner: string;
    tos: ToS;
    permanent: boolean;
    network: Network;
    root_user: RootUser;
    request_detail: RequestDetail;
  }

  export interface RootUser {
    password_hash: string;
    ssh_public_key: string;
    mgmt_ssh_public_key: string;
    mgmt_ssh_private_key: string;
  }

  export interface RequestDetail {
    template_id: string;
    reason: string;
  }

  export interface ToS {
    suspended: boolean;
    reason: string;
  }

  export interface Network {
    ports: { [external: number]: number };
    vhosts: { [vhost: string]: VHostOptions };
    nic_allocation: NICAllocation;
  }

  export interface VHostOptions {
    port: number;
    https: boolean;
  }

  export interface NICAllocation {
    addresses: string[];
    gateway4: string;
    macaddress: string;
  }

  export interface Request {
    username: string;
    hostname: string;
    type: Type;
    detail: RequestDetail;
  }

  export interface VHostRequirements {
    base_domain: string;
    user_supplied: {
      verification_text_name: string;
      allowed_a_aaaa: string[];
    };
  }

  export interface TemplateMetadata {
    title: string;
    subtitle: string;
    description: string;
    logo_url: string;
  }

  export interface Template {
    metadata: TemplateMetadata;
    specs: Specs;
  }

  export interface File {
    st_size: number;
    st_uid: number;
    st_gid: number;
    st_mode: number;
    st_atime: number;
    st_mtime: number;
    group: string;
    owner: string;
  }
}